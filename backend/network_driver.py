"""A PixelDriver that streams frames to a device over the network.

This driver is the client; The device is the WebSocket server. 

The wire format is specified in docs/docs/network-pixel-protocol.md 
Frame data and the device's readiness signal ride one WebSocket connection,
`/status` and `/clear` stay plain HTTP.

Kept in its own module (rather than pixel_driver.py) so that `requests` and
`websockets` are only required when a NetworkPixelDriver is actually used."""

import queue
import struct
import threading
import time
from typing import Optional

import numpy as np
import requests
from requests.adapters import HTTPAdapter
from websockets.exceptions import ConnectionClosed, WebSocketException
from websockets.sync.client import ClientConnection, connect

from pixel_driver import BUFFER, PREROLL, PixelDriver

TYPE_FRAME = 0x01
TYPE_CREDIT = 0x02

# Big-endian: type(1) seq(4) presentation_time_us(8)
_FRAME_HEADER = struct.Struct(">BIq")
# Big-endian: type(1) free_slots(4)
_CREDIT = struct.Struct(">BI")


class NetworkPixelDriver(PixelDriver):
    """Sends frames to a device speaking the GRIDmas network pixel protocol.

    The device reports how many frames it currently has room for this driver
    only sends up to that many frames ahead, decrementing its local copy as
    it sends and topping up whenever a new CREDIT snapshot arrives. A fresh
    or reconnected connection starts at zero credit until the device's
    first snapshot.
    """

    DEFAULT_PORT = 8420
    HTTP_TIMEOUT_S = 0.5
    # A lost initial SYN over Wi-Fi is routine, not exceptional - the OS's own
    # default initial SYN retransmit timeout (RFC 6298) is ~1s, so a 1.0s
    # connect timeout here raced that retransmission and lost about half the
    # time (confirmed: failures landed at exactly ~1.00s, i.e. no response at
    # all rather than a fast refusal). 3s comfortably covers one retransmit.
    CONNECT_TIMEOUT_S = 3.0
    RECV_TIMEOUT_S = 2.0
    RECONNECT_BACKOFF_S = 1.0

    # A frame more than this many seconds past its presentation time is
    # dropped client-side rather than sent, matching the device's own
    # late-grace window.
    LATE_GRACE_S = 0.25

    def __init__( self, address: str, pixel_count: int, name: str, fps: int, port: int=DEFAULT_PORT):
        super().__init__(pixel_count, name, fps)
        self._address = address
        self.port = port
        self._base_url = f"http://{address}:{port}"
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

    def inc_stat(self, key: str, n: int = 1):
        with self._stats_lock:
            self._stats[key] += n

    def flush(self, t: float):
        """Queue a frame to be sent to the device.

        never blocks on the network - it hands each frame to a
        background connection thread over a small bounded queue, so a slow or
        unreachable device can't stall pattern computation for every other
        registered driver. If the queue is full, the *oldest* queued frame is
        dropped in favour of the new one; a frame whose presentation time has
        already passed (plus a small grace) is dropped rather than sent, since
        the device would only drop it as late anyway.

        Args:
            t (float): The unix timestamp (seconds) this frame should be shown at.
        """
        payload = np.asarray(self.pixel_buffer, dtype=np.uint8).tobytes()
        self._seq += 1
        item = (self._seq, t, payload)
        try:
            self._out_queue.put_nowait(item)
            self.inc_stat("queued")
        except queue.Full:
            try:
                self._out_queue.get_nowait()
                self.inc_stat("dropped_queue_full")
            except queue.Empty:
                pass
            try:
                self._out_queue.put_nowait(item)
                self.inc_stat("queued")
            except queue.Full:
                self.inc_stat("dropped_queue_full")

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
        """keeps the connection alive, dispatches recv threads and starts send thread"""
        consecutive_failures = 0
        while not self._stop.is_set():
            try:
                ws = connect(
                    f"ws://{self._address}:{self.port}/",
                    open_timeout=self.CONNECT_TIMEOUT_S,
                    ping_interval=None, # TODO re-enable once devices can do this
                    close_timeout=0.5,
                    compression=None,
                    max_size=None,
                )
            except (OSError, WebSocketException) as e:
                consecutive_failures += 1
                print(f"[{self.name}] connect failed ({consecutive_failures} in a row): {e}")
                self._stop.wait(self.RECONNECT_BACKOFF_S)
                continue

            if consecutive_failures:
                print(f"[{self.name}] connected after {consecutive_failures} failed attempt(s)")
                consecutive_failures = 0

            with self._credit_cv:
                self._credit = 0

            broken = threading.Event()
            recv_thread = threading.Thread(
                target=self._recv_loop, args=(ws, broken), name=f"{self.name}-ws-recv", daemon=True
            )
            recv_thread.start()
            self._send_loop(ws, broken)

            broken.set()
            ws.close()
            recv_thread.join(timeout=self.RECV_TIMEOUT_S)
            if not self._stop.is_set():
                self.inc_stat("reconnects")

    def _send_loop(self, ws: ClientConnection, broken: threading.Event):
        while not self._stop.is_set() and not broken.is_set():
            try:
                seq, t, payload = self._out_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if t < time.time() - self.LATE_GRACE_S:
                self.inc_stat("dropped_late")
                continue

            with self._credit_cv:
                while self._credit <= 0 and not self._stop.is_set() and not broken.is_set():
                    self._credit_cv.wait(timeout=0.5)
                if self._stop.is_set() or broken.is_set():
                    return
                self._credit -= 1

            datagram = _FRAME_HEADER.pack(TYPE_FRAME, seq & 0xFFFFFFFF, int(t * 1_000_000)) + payload
            try:
                ws.send(datagram)
                self.inc_stat("sent")
            except (OSError, ConnectionClosed) as e:
                self.inc_stat("failed")
                print(f"[{self.name}] failed to send frame {seq}: {e}")
                broken.set()
                return
            except Exception as e:
                self.inc_stat("failed")
                print(f"[{self.name}] unexpected error sending frame {seq}: {e}")

    def _recv_loop(self, ws: ClientConnection, broken: threading.Event):
        while not self._stop.is_set() and not broken.is_set():
            try:
                msg = ws.recv(timeout=self.RECV_TIMEOUT_S)
            except (OSError, ConnectionClosed) as e:
                if not self._stop.is_set():
                    print(f"[{self.name}] WS recv failed: {e}")
                break
            except Exception as e:
                print(f"[{self.name}] unexpected error handling a WS message: {e}")
                break

            if not isinstance(msg, bytes) or len(msg) != _CREDIT.size or msg[0] != TYPE_CREDIT:
                continue

            _, free_slots = _CREDIT.unpack(msg)
            with self._credit_cv:
                self._credit = free_slots
                self._credit_cv.notify_all()

        broken.set()
        with self._credit_cv:
            self._credit_cv.notify_all()
