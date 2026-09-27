"""The device side of the GRIDmas Tree network pixel protocol
(docs/docs/network-pixel-protocol.md) - one TCP listener serving both halves:

- plain HTTP requests: `GET /status` and `POST /clear` (keep-alive), and
- a WebSocket upgrade (any `GET` carrying `Sec-WebSocket-Key`), after which
  that connection becomes the frame data plane: FRAME messages are handed
  to the scheduler for playback, and the scheduler's free-slot count is
  reported back as CREDIT messages so the controller knows how much it's
  allowed to send.

Every connection starts as HTTP and is routed by its request headers, so
there's no second port. Only one controller streams frames at a time - a
new WS upgrade tears down whichever connection was previously active.
See backend/network_driver.py for the client.
"""

from __future__ import annotations

import base64
import hashlib
import json
import socket
import struct
import threading
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from scheduler import FrameScheduler, Strip

FIRMWARE_VERSION = "1.0.0"

TYPE_FRAME = 0x01
TYPE_CREDIT = 0x02

# Big-endian: type(1) seq(4) presentation_time_us(8)
_FRAME_HEADER = struct.Struct(">BIq")
# Big-endian: type(1) free_slots(4)
_CREDIT = struct.Struct(">BI")

_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_OPCODE_BINARY = 0x2
_OPCODE_CLOSE = 0x8

_POLL_S = 0.1
_HEARTBEAT_S = 0.3  # re-send credit even if unchanged, so silence is meaningful
_HTTP_IDLE_TIMEOUT_S = 30.0  # close keep-alive connections idle this long
_MAX_HEADER_BYTES = 8192


def _accept_key(client_key: str) -> str:
    digest = hashlib.sha1((client_key + _WS_GUID).encode()).digest()
    return base64.b64encode(digest).decode()


def _unmask(payload: bytes, mask: bytes) -> bytes:
    # XOR as one big int rather than byte-by-byte - a 1500-byte frame at
    # 45fps is noticeable CPU on a Pi in a Python-level loop
    n = len(payload)
    key = (mask * (n // 4 + 1))[:n]
    return (int.from_bytes(payload, "big") ^ int.from_bytes(key, "big")).to_bytes(n, "big")


class _Reader:
    """Buffered reads off a socket, so bytes that arrive past the end of an
    HTTP request (the next keep-alive request, or the first WS frame after
    an upgrade) aren't lost."""

    def __init__(self, conn: socket.socket):
        self._conn = conn
        self._buf = bytearray()

    def _fill(self):
        chunk = self._conn.recv(65536)
        if not chunk:
            raise ConnectionError("connection closed")
        self._buf += chunk

    def read_until(self, delim: bytes, limit: int) -> bytes:
        while True:
            i = self._buf.find(delim)
            if i >= 0:
                out = bytes(self._buf[:i + len(delim)])
                del self._buf[:i + len(delim)]
                return out
            if len(self._buf) > limit:
                raise ConnectionError("request headers too large")
            self._fill()

    def read_exact(self, n: int) -> bytes:
        while len(self._buf) < n:
            self._fill()
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out


def _parse_request(head: bytes) -> "tuple[str, str, dict]":
    lines = head.decode("latin-1").split("\r\n")
    parts = lines[0].split(" ")
    if len(parts) < 3:
        raise ConnectionError(f"malformed request line: {lines[0]!r}")
    headers = {}
    for line in lines[1:]:
        key, sep, value = line.partition(":")
        if sep:
            headers[key.strip().lower()] = value.strip()
    return parts[0].upper(), parts[1], headers


def _recv_ws_frame(reader: _Reader) -> "tuple[int, bytes]":
    b1, b2 = reader.read_exact(2)
    opcode = b1 & 0x0F
    length = b2 & 0x7F
    if length == 126:
        length = struct.unpack(">H", reader.read_exact(2))[0]
    elif length == 127:
        length = struct.unpack(">Q", reader.read_exact(8))[0]
    mask = reader.read_exact(4) if b2 & 0x80 else None
    payload = reader.read_exact(length)
    if mask:
        payload = _unmask(payload, mask)
    return opcode, payload


def _send_ws_frame(conn: socket.socket, opcode: int, payload: bytes):
    """Server-to-client frames must not be masked (RFC 6455 5.1)."""
    length = len(payload)
    if length <= 125:
        header = bytes([0x80 | opcode, length])
    elif length <= 0xFFFF:
        header = bytes([0x80 | opcode, 126]) + struct.pack(">H", length)
    else:
        header = bytes([0x80 | opcode, 127]) + struct.pack(">Q", length)
    conn.sendall(header + payload)


def _close(conn: socket.socket):
    # shutdown() first: close() alone doesn't wake a thread blocked in recv()
    # on this socket (on Linux), shutdown() does
    try:
        conn.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        conn.close()
    except OSError:
        pass


class DeviceServer:
    """Owns the device's single TCP listener.

    Each accepted connection gets a thread that serves HTTP requests on it
    until it either closes or upgrades to WebSocket. An upgraded connection
    becomes the active frame connection: that same thread turns into its
    receiver (parses FRAME messages) and a second credit-reporter thread
    sends free-slot snapshots on change and on a heartbeat. Both exit once
    a newer upgrade replaces their connection or the server stops.
    """

    def __init__(self, strip: Strip, scheduler: FrameScheduler, device_name: str, target_fps: int, port: int):
        self._strip = strip
        self._scheduler = scheduler
        self._device_name = device_name
        self._target_fps = target_fps
        self._started = time.time()

        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind(("0.0.0.0", port))
        self._listener.listen(8)
        self._listener.settimeout(_POLL_S)

        self._stop = threading.Event()
        self._accept_thread = threading.Thread(target=self._accept_loop, name="device-accept", daemon=True)

        self._active_lock = threading.Lock()
        self._active_conn: Optional[socket.socket] = None

    def start(self):
        self._accept_thread.start()

    def stop(self):
        self._stop.set()
        self._accept_thread.join(timeout=1)
        with self._active_lock:
            old, self._active_conn = self._active_conn, None
        if old is not None:
            _close(old)
        self._listener.close()

    def _accept_loop(self):
        while not self._stop.is_set():
            try:
                conn, _addr = self._listener.accept()
            except socket.timeout:
                continue
            except OSError as e:
                if self._stop.is_set():
                    return
                print(f"device: accept error: {e}")
                self._stop.wait(0.05)
                continue
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            threading.Thread(target=self._serve_conn, args=(conn,), name="device-conn", daemon=True).start()

    def _serve_conn(self, conn: socket.socket):
        # The except Exception here is a deliberate safety net: one
        # malformed request or unexpected bug must only ever cost the one
        # connection it happened on, never the server.
        try:
            conn.settimeout(_HTTP_IDLE_TIMEOUT_S)
            reader = _Reader(conn)
            while not self._stop.is_set():
                method, path, headers = _parse_request(reader.read_until(b"\r\n\r\n", _MAX_HEADER_BYTES))
                body_len = int(headers.get("content-length", "0") or 0)
                if body_len:
                    reader.read_exact(body_len)  # neither route takes a body

                if method == "GET" and "sec-websocket-key" in headers:
                    self._upgrade(conn, reader, headers["sec-websocket-key"])
                    return
                keep_alive = headers.get("connection", "").lower() != "close"
                self._handle_http(conn, method, path, keep_alive)
                if not keep_alive:
                    return
        except (OSError, ConnectionError):
            pass  # client went away or idled out - routine for HTTP
        except Exception as e:
            print(f"device: unexpected error on a connection: {e}")
        finally:
            with self._active_lock:
                if conn is self._active_conn:
                    self._active_conn = None
            _close(conn)

    # -- HTTP control plane --

    def _handle_http(self, conn: socket.socket, method: str, path: str, keep_alive: bool):
        if method == "GET" and path == "/status":
            body = json.dumps(self._status()).encode()
            self._respond(conn, "200 OK", body, "application/json", keep_alive)
        elif method == "POST" and path == "/clear":
            self._scheduler.clear()
            self._respond(conn, "200 OK", b"", "text/plain", keep_alive)
        else:
            self._respond(conn, "404 Not Found", b"not found", "text/plain", keep_alive)

    @staticmethod
    def _respond(conn: socket.socket, status: str, body: bytes, content_type: str, keep_alive: bool):
        head = (
            f"HTTP/1.1 {status}\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Connection: {'keep-alive' if keep_alive else 'close'}\r\n\r\n"
        )
        conn.sendall(head.encode() + body)

    def _status(self) -> dict:
        now = time.time()
        return {
            "device_name": self._device_name,
            "pixel_count": self._strip.pixel_count,
            "target_fps": self._target_fps,
            "firmware_version": FIRMWARE_VERSION,
            "uptime_s": now - self._started,
            "clock": now,
            "queue": {"depth": self._scheduler.depth(), "capacity": self._scheduler.capacity},
            "stats": self._scheduler.snapshot_stats(),
        }

    # -- WebSocket data plane --

    def _upgrade(self, conn: socket.socket, reader: _Reader, client_key: str):
        """Server side of the WS handshake (RFC 6455 1.3), then serve frames
        on this connection until it closes or is replaced."""
        conn.sendall((
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {_accept_key(client_key)}\r\n\r\n"
        ).encode())

        # swap before closing, so the old connection's threads already see
        # they've been replaced when _close() wakes them
        with self._active_lock:
            old, self._active_conn = self._active_conn, conn
        if old is not None:
            print("device: new frame connection replaces the current one")
            _close(old)

        # no read timeout from here on: a quiet controller is fine, and a
        # replaced/stopped connection is woken by _close()'s shutdown()
        conn.settimeout(None)
        threading.Thread(target=self._credit_loop, args=(conn,), name="device-credit", daemon=True).start()
        self._recv_loop(conn, reader)

    def _recv_loop(self, conn: socket.socket, reader: _Reader):
        while not self._stop.is_set() and conn is self._active_conn:
            try:
                opcode, payload = _recv_ws_frame(reader)
            except (OSError, ConnectionError) as e:
                if conn is self._active_conn:
                    print(f"device: frame recv error: {e}")
                return

            if opcode == _OPCODE_CLOSE:
                return
            if opcode != _OPCODE_BINARY or len(payload) < _FRAME_HEADER.size or payload[0] != TYPE_FRAME:
                continue

            _, seq, t_us = _FRAME_HEADER.unpack_from(payload)
            self._scheduler.submit_frame(t_us / 1_000_000, seq, payload[_FRAME_HEADER.size:])

    def _credit_loop(self, conn: socket.socket):
        # Same safety-net reasoning as _serve_conn: an unexpected bug here
        # must not leave the controller waiting on credit forever - close
        # the connection so it reconnects instead.
        last_sent: Optional[int] = None
        last_sent_at = 0.0
        try:
            while not self._stop.is_set() and conn is self._active_conn:
                free_slots = self._scheduler.free_slots()
                now = time.time()
                if free_slots != last_sent or now - last_sent_at >= _HEARTBEAT_S:
                    _send_ws_frame(conn, _OPCODE_BINARY, _CREDIT.pack(TYPE_CREDIT, free_slots))
                    last_sent = free_slots
                    last_sent_at = now
                self._stop.wait(_POLL_S)
        except OSError as e:
            if conn is self._active_conn:
                print(f"device: failed to send credit: {e}")
                _close(conn)
        except Exception as e:
            print(f"device: unexpected error sending credit: {e}")
            _close(conn)
