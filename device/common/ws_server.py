"""WebSocket server - the data-plane half of the network pixel protocol
(docs/docs/network-pixel-protocol.md). `/status` and `/clear` stay on HTTP
(see app.py); this module owns the WS listener for everything else:
receiving FRAME messages (handed to the scheduler for playback) and
reporting the scheduler's free-slot count back to the controller, so it
knows how much it's allowed to send.

Only one controller talks to a device at a time - accepting a new
connection tears down whichever one was previously active.
"""

import base64
import hashlib
import socket
import struct
import threading
import time
from typing import Optional

from scheduler import FrameScheduler

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


def _accept_key(client_key: str) -> str:
    digest = hashlib.sha1((client_key + _WS_GUID).encode()).digest()
    return base64.b64encode(digest).decode()


def _read_upgrade_headers(conn: socket.socket) -> dict:
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = conn.recv(4096)
        if not chunk:
            raise ConnectionError("client closed connection during WS handshake")
        data += chunk
    headers = {}
    for line in data.split(b"\r\n\r\n", 1)[0].split(b"\r\n")[1:]:
        if b":" not in line:
            continue
        key, _, value = line.partition(b":")
        headers[key.strip().lower().decode()] = value.strip().decode()
    return headers


def _handshake(conn: socket.socket):
    """Server side of the WS handshake (RFC 6455 1.3)."""
    headers = _read_upgrade_headers(conn)
    key = headers.get("sec-websocket-key")
    if key is None:
        raise ConnectionError("not a WebSocket upgrade request")
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\nConnection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {_accept_key(key)}\r\n\r\n"
    )
    conn.sendall(response.encode())


def _recv_exact(conn: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("connection closed")
        buf += chunk
    return bytes(buf)


def _recv_ws_frame(conn: socket.socket) -> "tuple[int, bytes]":
    b1, b2 = _recv_exact(conn, 2)
    opcode = b1 & 0x0F
    length = b2 & 0x7F
    if length == 126:
        length = struct.unpack(">H", _recv_exact(conn, 2))[0]
    elif length == 127:
        length = struct.unpack(">Q", _recv_exact(conn, 8))[0]
    mask = _recv_exact(conn, 4) if b2 & 0x80 else None
    payload = _recv_exact(conn, length)
    if mask:
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
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


class WsFrameServer:
    """Owns the TCP listener for the frame data plane.

    Each accepted connection gets its own receiver thread (parses incoming
    FRAME messages) and credit-reporter thread (sends free-slot snapshots
    on change and on a heartbeat). Both threads exit once a newer
    connection replaces theirs or the server stops.
    """

    def __init__(self, scheduler: FrameScheduler, port: int):
        self._scheduler = scheduler
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind(("0.0.0.0", port))
        self._listener.listen(1)
        self._listener.settimeout(_POLL_S)

        self._stop = threading.Event()
        self._accept_thread = threading.Thread(target=self._accept_loop, name="ws-frame-accept", daemon=True)

        self._active_conn: Optional[socket.socket] = None
        self._active_threads: "list[threading.Thread]" = []

    def start(self):
        self._accept_thread.start()

    def stop(self):
        self._stop.set()
        self._accept_thread.join(timeout=1)
        self._close_active()
        self._listener.close()

    def _close_active(self):
        if self._active_conn is not None:
            try:
                self._active_conn.close()
            except OSError:
                pass
        for t in self._active_threads:
            t.join(timeout=1)
        self._active_conn = None
        self._active_threads = []

    def _accept_loop(self):
        # The outer except Exception in each loop below is a deliberate
        # safety net: these threads run for the life of the device, and one
        # malformed message or unexpected bug can't silently kill frame
        # reception (or credit reporting) for good.
        while not self._stop.is_set():
            try:
                conn, _addr = self._listener.accept()
            except socket.timeout:
                continue
            except OSError as e:
                if self._stop.is_set():
                    return
                print(f"ws-frame: accept error: {e}")
                self._stop.wait(0.05)
                continue

            try:
                _handshake(conn)
            except Exception as e:
                print(f"ws-frame: handshake failed: {e}")
                conn.close()
                continue

            self._close_active()
            conn.settimeout(_POLL_S)
            self._active_conn = conn
            recv_thread = threading.Thread(target=self._recv_loop, args=(conn,), name="ws-frame-recv", daemon=True)
            credit_thread = threading.Thread(
                target=self._credit_loop, args=(conn,), name="ws-frame-credit", daemon=True
            )
            self._active_threads = [recv_thread, credit_thread]
            recv_thread.start()
            credit_thread.start()

    def _recv_loop(self, conn: socket.socket):
        while not self._stop.is_set() and conn is self._active_conn:
            try:
                opcode, payload = _recv_ws_frame(conn)
            except socket.timeout:
                continue
            except (OSError, ConnectionError) as e:
                if conn is self._active_conn:
                    print(f"ws-frame: recv error: {e}")
                return
            except Exception as e:
                print(f"ws-frame: unexpected error handling a message: {e}")
                return

            if opcode == _OPCODE_CLOSE:
                return
            if opcode != _OPCODE_BINARY or len(payload) < _FRAME_HEADER.size or payload[0] != TYPE_FRAME:
                continue

            _, seq, t_us = _FRAME_HEADER.unpack_from(payload)
            self._scheduler.submit_frame(t_us / 1_000_000, seq, payload[_FRAME_HEADER.size:])

    def _credit_loop(self, conn: socket.socket):
        last_sent: Optional[int] = None
        last_sent_at = 0.0
        while not self._stop.is_set() and conn is self._active_conn:
            free_slots = self._scheduler.free_slots()
            now = time.time()
            if free_slots != last_sent or now - last_sent_at >= _HEARTBEAT_S:
                try:
                    _send_ws_frame(conn, _OPCODE_BINARY, _CREDIT.pack(TYPE_CREDIT, free_slots))
                except OSError as e:
                    if conn is self._active_conn:
                        print(f"ws-frame: failed to send credit: {e}")
                    return
                except Exception as e:
                    print(f"ws-frame: unexpected error sending credit: {e}")
                    return
                last_sent = free_slots
                last_sent_at = now
            self._stop.wait(_POLL_S)
