"""A PixelDriver that streams frames to a physical LED controller (e.g. a
Raspberry Pi driving a WS2812 strip) over the network.

The device is the WebSocket server; this driver is the client. The wire
format is specified in docs/docs/network-pixel-protocol.md - this module is
the reference implementation of the controller side of that spec: frame
data and the device's readiness signal ride one WebSocket connection,
`/status` and `/clear` stay plain HTTP.

Kept in its own module (rather than pixel_driver.py) so that `requests` is
only required when a NetworkPixelDriver is actually used. GMT2025back.py
imports pixel_driver.py unconditionally, including under Pyodide (the web
editor), where `requests` isn't installed.
"""

import base64
import os
import queue
import socket
import struct
import threading
import time
from typing import Optional

import numpy as np
import requests
from requests.adapters import HTTPAdapter

from pixel_driver import BUFFER, PREROLL, PixelDriver

# -- Wire format (docs/docs/network-pixel-protocol.md) --
TYPE_FRAME = 0x01
TYPE_CREDIT = 0x02

# Big-endian: type(1) seq(4) presentation_time_us(8)
_FRAME_HEADER = struct.Struct(">BIq")
# Big-endian: type(1) free_slots(4)
_CREDIT = struct.Struct(">BI")

_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_OPCODE_BINARY = 0x2
_OPCODE_CLOSE = 0x8


def _ws_connect(address: str, port: int, timeout: float) -> socket.socket:
    """Open a TCP connection and perform the WS client handshake (RFC 6455 1.3).

    Raises OSError (a plain socket.timeout/TimeoutError included) tagged with
    which phase it happened in - "TCP connect" vs "WS handshake response" -
    since both look identical from the caller's generic `except OSError`
    otherwise, and they point at very different root causes (unreachable/
    down device vs. a device that accepted the connection but is slow or
    stuck to respond).
    """
    t0 = time.monotonic()
    try:
        sock = socket.create_connection((address, port), timeout=timeout)
    except OSError as e:
        raise OSError(f"TCP connect after {time.monotonic() - t0:.2f}s: {e}") from e

    key = base64.b64encode(os.urandom(16)).decode()
    request = (
        f"GET / HTTP/1.1\r\nHost: {address}:{port}\r\n"
        "Upgrade: websocket\r\nConnection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
    )
    t1 = time.monotonic()
    try:
        sock.sendall(request.encode())
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = sock.recv(1024)
            if not chunk:
                raise ConnectionError("device closed connection during WS handshake")
            response += chunk
    except OSError as e:
        sock.close()
        raise OSError(f"WS handshake response after {time.monotonic() - t1:.2f}s: {e}") from e
    if not response.startswith(b"HTTP/1.1 101"):
        sock.close()
        raise ConnectionError(f"WS handshake rejected: {response!r}")
    return sock


def _send_ws_frame(sock: socket.socket, opcode: int, payload: bytes):
    """Client-to-server frames must be masked (RFC 6455 5.1)."""
    length = len(payload)
    if length <= 125:
        header = bytes([0x80 | opcode, 0x80 | length])
    elif length <= 0xFFFF:
        header = bytes([0x80 | opcode, 0x80 | 126]) + struct.pack(">H", length)
    else:
        header = bytes([0x80 | opcode, 0x80 | 127]) + struct.pack(">Q", length)
    mask = os.urandom(4)
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    sock.sendall(header + mask + masked)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("connection closed")
        buf += chunk
    return bytes(buf)


def _recv_ws_frame(sock: socket.socket) -> "tuple[int, bytes]":
    b1, b2 = _recv_exact(sock, 2)
    opcode = b1 & 0x0F
    length = b2 & 0x7F
    if length == 126:
        length = struct.unpack(">H", _recv_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack(">Q", _recv_exact(sock, 8))[0]
    mask = _recv_exact(sock, 4) if b2 & 0x80 else None
    payload = _recv_exact(sock, length)
    if mask:
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return opcode, payload


class NetworkPixelDriver(PixelDriver):
    """Sends frames to a device speaking the GRIDmas network pixel protocol.

    flush() never blocks on the network - it hands each frame to a
    background connection thread over a small bounded queue, so a slow or
    unreachable device can't stall pattern computation for every other
    registered driver. If the queue is full, the *oldest* queued frame is
    dropped in favour of the new one; a frame whose presentation time has
    already passed (plus a small grace) is dropped rather than sent, since
    the device would only drop it as late anyway.

    The device reports how many frames it currently has room for (a
    CREDIT message - see docs/docs/network-pixel-protocol.md); this driver
    only sends up to that many frames ahead, decrementing its local copy as
    it sends and topping up whenever a new CREDIT snapshot arrives. A fresh
    or reconnected connection starts at zero credit until the device's
    first snapshot.
    """

    DEFAULT_HTTP_PORT = 8420
    DEFAULT_WS_PORT = 8421
    HTTP_TIMEOUT_S = 0.5
    # A lost initial SYN over Wi-Fi is routine, not exceptional - the OS's own
    # default initial SYN retransmit timeout (RFC 6298) is ~1s, so a 1.0s
    # connect timeout here raced that retransmission and lost about half the
    # time (confirmed: failures landed at exactly ~1.00s, i.e. no response at
    # all rather than a fast refusal). 3s comfortably covers one retransmit.
    CONNECT_TIMEOUT_S = 3.0
    RECV_TIMEOUT_S = 2.0  # several heartbeat intervals - see ws_server.py's _HEARTBEAT_S
    RECONNECT_BACKOFF_S = 1.0

    # A frame more than this many seconds past its presentation time is
    # dropped client-side rather than sent, matching the device's own
    # late-grace window.
    LATE_GRACE_S = 0.25

    def __init__(
        self,
        address: str,
        pixel_count: int,
        name: str,
        fps: int,
        http_port: int = DEFAULT_HTTP_PORT,
        ws_port: int = DEFAULT_WS_PORT,
    ):
        super().__init__(pixel_count, name, fps)
        self._address = address
        self._ws_port = ws_port
        self._base_url = f"http://{address}:{http_port}"
        self._seq = 0

        self._session = self._make_http_session()

        frame_capacity = max(1, int(fps * (PREROLL + BUFFER)))
        self._out_queue: "queue.Queue[tuple[int, float, bytes]]" = queue.Queue(maxsize=frame_capacity)

        self._credit_lock = threading.Lock()
        self._credit_cv = threading.Condition(self._credit_lock)
        self._credit = 0

        self._stats_lock = threading.Lock()
        self._stats = {
            "queued": 0,
            "sent": 0,
            "dropped_queue_full": 0,
            "dropped_late": 0,
            "failed": 0,
            "reconnects": 0,
        }

        self._stop = threading.Event()
        self._conn_thread = threading.Thread(target=self._connection_loop, name=f"{name}-ws", daemon=True)
        self._conn_thread.start()

    @staticmethod
    def _make_http_session() -> requests.Session:
        """A Session with one kept-alive connection and no retries, for the
        infrequent /status and /clear calls only."""
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=1)
        session.mount("http://", adapter)
        return session

    def _bump(self, key: str, n: int = 1):
        with self._stats_lock:
            self._stats[key] += n

    def flush(self, frame: np.ndarray, t: float):
        """Queue a frame to be sent to the device.

        Args:
            frame (np.ndarray): An (N, 3) array of uint8 RGB triples, one per pixel.
            t (float): The unix timestamp (seconds) this frame should be shown at.
        """
        payload = np.asarray(frame, dtype=np.uint8).tobytes()
        self._seq += 1
        item = (self._seq, t, payload)
        try:
            self._out_queue.put_nowait(item)
            self._bump("queued")
        except queue.Full:
            try:
                self._out_queue.get_nowait()
                self._bump("dropped_queue_full")
            except queue.Empty:
                pass
            try:
                self._out_queue.put_nowait(item)
                self._bump("queued")
            except queue.Full:
                self._bump("dropped_queue_full")

    def stats(self) -> dict:
        """A snapshot of this driver's send counters, for diagnostics.

        Returns:
            dict: Cumulative counts - queued, sent, dropped_queue_full,
                dropped_late, failed (local socket error), reconnects -
                plus the device's most recently reported free-slot credit.
        """
        with self._stats_lock:
            snapshot = dict(self._stats)
        with self._credit_cv:
            snapshot["credit"] = self._credit
        return snapshot

    def status(self) -> Optional[dict]:
        """GET /status from the device.

        Returns:
            dict | None: The device's parsed status response, or None if it's unreachable.
        """
        try:
            resp = self._session.get(f"{self._base_url}/status", timeout=self.HTTP_TIMEOUT_S)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"[{self.name}] status check failed: {e}")
            return None

    def close(self):
        """Stop the connection thread and ask the device to blank its pixels."""
        self._stop.set()
        with self._credit_cv:
            self._credit_cv.notify_all()
        self._conn_thread.join(timeout=self.CONNECT_TIMEOUT_S + self.HTTP_TIMEOUT_S)
        try:
            self._session.post(f"{self._base_url}/clear", timeout=self.HTTP_TIMEOUT_S)
        except requests.RequestException:
            pass

    def _connection_loop(self):
        # The outer except Exception in each helper below is a deliberate
        # safety net: these threads run for the life of the driver, and one
        # bad/unexpected item must never silently kill frame delivery to a
        # fixture for good.
        #
        # Frames queued while disconnected (or mid-handshake) are not
        # explicitly purged on (re)connect - the per-frame late check in
        # _send_loop already drops anything whose presentation time has
        # passed by the time it's actually its turn to send, which is a
        # more accurate staleness test than "which connection was this
        # queued during".
        consecutive_failures = 0
        while not self._stop.is_set():
            try:
                sock = _ws_connect(self._address, self._ws_port, self.CONNECT_TIMEOUT_S)
            except OSError as e:
                consecutive_failures += 1
                print(f"[{self.name}] connect failed ({consecutive_failures} in a row): {e}")
                self._stop.wait(self.RECONNECT_BACKOFF_S)
                continue

            if consecutive_failures:
                print(f"[{self.name}] connected after {consecutive_failures} failed attempt(s)")
                consecutive_failures = 0

            sock.settimeout(self.RECV_TIMEOUT_S)
            with self._credit_cv:
                self._credit = 0

            broken = threading.Event()
            recv_thread = threading.Thread(
                target=self._recv_loop, args=(sock, broken), name=f"{self.name}-ws-recv", daemon=True
            )
            recv_thread.start()
            self._send_loop(sock, broken)

            broken.set()
            try:
                sock.close()
            except OSError:
                pass
            recv_thread.join(timeout=self.RECV_TIMEOUT_S)
            if not self._stop.is_set():
                self._bump("reconnects")

    def _send_loop(self, sock: socket.socket, broken: threading.Event):
        while not self._stop.is_set() and not broken.is_set():
            try:
                seq, t, payload = self._out_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if t < time.time() - self.LATE_GRACE_S:
                self._bump("dropped_late")
                continue

            with self._credit_cv:
                while self._credit <= 0 and not self._stop.is_set() and not broken.is_set():
                    self._credit_cv.wait(timeout=0.5)
                if self._stop.is_set() or broken.is_set():
                    return
                self._credit -= 1

            datagram = _FRAME_HEADER.pack(TYPE_FRAME, seq & 0xFFFFFFFF, int(t * 1_000_000)) + payload
            try:
                _send_ws_frame(sock, _OPCODE_BINARY, datagram)
                self._bump("sent")
            except OSError as e:
                self._bump("failed")
                print(f"[{self.name}] failed to send frame {seq}: {e}")
                broken.set()
                return
            except Exception as e:
                self._bump("failed")
                print(f"[{self.name}] unexpected error sending frame {seq}: {e}")

    def _recv_loop(self, sock: socket.socket, broken: threading.Event):
        while not self._stop.is_set() and not broken.is_set():
            try:
                opcode, payload = _recv_ws_frame(sock)
            except (OSError, ConnectionError) as e:
                if not self._stop.is_set():
                    print(f"[{self.name}] WS recv failed: {e}")
                break
            except Exception as e:
                print(f"[{self.name}] unexpected error handling a WS message: {e}")
                break

            if opcode == _OPCODE_CLOSE:
                break
            if opcode != _OPCODE_BINARY or len(payload) != _CREDIT.size or payload[0] != TYPE_CREDIT:
                continue

            _, free_slots = _CREDIT.unpack(payload)
            with self._credit_cv:
                self._credit = free_slots
                self._credit_cv.notify_all()

        broken.set()
        with self._credit_cv:
            self._credit_cv.notify_all()
