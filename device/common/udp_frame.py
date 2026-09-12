"""UDP frame receiver + NAK sender - the data-plane half of the network
pixel protocol (docs/docs/network-pixel-protocol.md). `/status` and
`/clear` stay on HTTP (see app.py); this module owns the one UDP socket
used for everything else: receiving FRAME datagrams (handed to the
scheduler for reassembly) and sending NAK datagrams back to the controller
when the scheduler flags a gap.

There's no separate "control port" for NAKs - they go back to whatever
(address, port) the most recent FRAME datagram arrived from, which is
exactly what a NetworkPixelDriver's connected UDP socket already listens on.
"""

import socket
import struct
import threading
from typing import Optional, Tuple

from scheduler import FrameScheduler

TYPE_FRAME = 0x01
TYPE_NAK = 0x02

# Big-endian: type(1) seq(4) presentation_time_us(8) chunk_index(1) chunk_count(1)
_FRAME_HEADER = struct.Struct(">BIqBB")
# Big-endian: type(1) seq(4) chunk_index(1)
_NAK = struct.Struct(">BIB")

_POLL_S = 0.2  # both the recv-socket timeout and the NAK-queue poll interval


class UdpFrameServer:
    """Owns the UDP socket for the frame data plane.

    Two threads share the one bound socket: one blocks on recvfrom() and
    feeds chunks to the scheduler (a single receiver is enough - per-datagram
    handling is cheap, and this mirrors the sender side only needing one
    thread now that sends don't block on a round trip either); the other
    polls the scheduler for chunks it wants retransmitted and sends the
    corresponding NAKs.
    """

    def __init__(self, scheduler: FrameScheduler, port: int):
        self._scheduler = scheduler
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(("0.0.0.0", port))
        self._sock.settimeout(_POLL_S)

        self._last_sender: Optional[Tuple[str, int]] = None
        self._last_sender_lock = threading.Lock()

        self._stop = threading.Event()
        self._recv_thread = threading.Thread(target=self._recv_loop, name="udp-frame-recv", daemon=True)
        self._nak_thread = threading.Thread(target=self._nak_loop, name="udp-frame-nak", daemon=True)

    def start(self):
        self._recv_thread.start()
        self._nak_thread.start()

    def stop(self):
        self._stop.set()
        self._recv_thread.join(timeout=1)
        self._nak_thread.join(timeout=1)
        self._sock.close()

    def _recv_loop(self):
        # Both loops below run for the life of the device; the broad
        # except Exception in each is a deliberate safety net so one
        # malformed datagram or unexpected bug can't silently kill frame
        # reception (or NAKs) for good.
        while not self._stop.is_set():
            try:
                datagram, addr = self._sock.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError as e:
                if self._stop.is_set():
                    return
                print(f"udp-frame: recv error: {e}")
                self._stop.wait(0.05)  # avoid spinning if this keeps failing
                continue

            try:
                if len(datagram) < _FRAME_HEADER.size or datagram[0] != TYPE_FRAME:
                    continue
                _, seq, t_us, chunk_index, chunk_count = _FRAME_HEADER.unpack_from(datagram)
                payload = datagram[_FRAME_HEADER.size:]
                if len(payload) % 3 != 0:
                    continue

                with self._last_sender_lock:
                    self._last_sender = addr

                self._scheduler.submit_chunk(t_us / 1_000_000, seq, chunk_index, chunk_count, payload)
            except Exception as e:
                print(f"udp-frame: unexpected error handling a datagram: {e}")

    def _nak_loop(self):
        while not self._stop.is_set():
            self._stop.wait(_POLL_S)  # doubles as the sleep between polls
            try:
                naks = self._scheduler.collect_naks()
                if not naks:
                    continue

                with self._last_sender_lock:
                    addr = self._last_sender
                if addr is None:
                    continue  # haven't heard from a controller yet, nowhere to send

                for seq, chunk_index in naks:
                    try:
                        self._sock.sendto(_NAK.pack(TYPE_NAK, seq & 0xFFFFFFFF, chunk_index), addr)
                    except OSError as e:
                        print(f"udp-frame: failed to send NAK for seq {seq} chunk {chunk_index}: {e}")
            except Exception as e:
                print(f"udp-frame: unexpected error sending NAKs: {e}")
