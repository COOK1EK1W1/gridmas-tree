"""A PixelDriver that streams frames to a physical LED controller (e.g. a
Raspberry Pi driving a WS2812 strip) over the network.

The device is the server; this driver is the client. The wire format is
specified in docs/docs/network-pixel-protocol.md - this module is the
reference implementation of the controller side of that spec: frame data
(and the retransmission requests that ride alongside it) go over UDP,
`/status` and `/clear` stay plain HTTP.

Kept in its own module (rather than pixel_driver.py) so that `requests` is
only required when a NetworkPixelDriver is actually used. GMT2025back.py
imports pixel_driver.py unconditionally, including under Pyodide (the web
editor), where `requests` isn't installed.
"""

import queue
import socket
import struct
import threading
import time
from collections import OrderedDict
from typing import Optional

import numpy as np
import requests
from requests.adapters import HTTPAdapter

from pixel_driver import BUFFER, PREROLL, PixelDriver

# -- Wire format (docs/docs/network-pixel-protocol.md) --
TYPE_FRAME = 0x01
TYPE_NAK = 0x02

# Big-endian: type(1) seq(4) presentation_time_us(8) chunk_index(1) chunk_count(1)
_FRAME_HEADER = struct.Struct(">BIqBB")
# Big-endian: type(1) seq(4) chunk_index(1)
_NAK = struct.Struct(">BIB")

PIXELS_PER_CHUNK = 480  # keeps every datagram under the ~1472B safe UDP payload


def _chunk_count(pixel_count: int) -> int:
    return max(1, -(-pixel_count // PIXELS_PER_CHUNK))  # ceil division


class NetworkPixelDriver(PixelDriver):
    """Sends frames to a device speaking the GRIDmas network pixel protocol.

    flush() never blocks on the network - it hands each frame (split into
    chunks, see docs/docs/network-pixel-protocol.md) to a background sender
    thread over a small bounded queue, so a slow or unreachable device can't
    stall pattern computation for every other registered driver.

    Two things keep a backlog from turning into visible lag:

    * If the queue is full, the *oldest* queued chunk is dropped in favour of
      the new one.
    * Before sending, the sender thread drops any chunk whose presentation
      time has already passed (plus a small grace) - the device would only
      drop it as late anyway (see FrameScheduler.late_grace_s in
      device/common/scheduler.py), so spending a send on it just wastes it.

    UDP's sendto() doesn't block on a round trip the way the old HTTP POST
    did, so a single sender thread is enough to sustain full frame rate -
    unlike the old HTTP client, which needed a pool of sender threads to get
    past TCP's one-connection-blocks-on-one-response throughput ceiling.

    A separate background thread listens on the same socket for
    retransmission requests (NAKs) from the device and re-sends the
    requested chunk from a small per-driver cache of recently-sent frames.
    """

    DEFAULT_PORT = 8420
    HTTP_TIMEOUT_S = 0.5

    # A chunk more than this many seconds past its frame's presentation time
    # is dropped client-side rather than sent. Matches the spirit of the
    # device's own late-grace window.
    LATE_GRACE_S = 0.25

    def __init__(
        self,
        address: str,
        pixel_count: int,
        name: str,
        fps: int,
        port: int = DEFAULT_PORT,
    ):
        super().__init__(pixel_count, name, fps)
        self._base_url = f"http://{address}:{port}"
        self._seq = 0
        self._chunk_count = _chunk_count(pixel_count)

        # requests.Session for the low-frequency HTTP control plane
        # (/status, /clear) only - the frame data path below is UDP.
        self._session = self._make_http_session()

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # connect() on a UDP socket just fixes the default peer for
        # send()/recv() and filters out datagrams from anyone else - there's
        # no handshake, it's still connectionless.
        self._sock.connect((address, port))
        self._sock.settimeout(0.2)  # so the NAK thread can notice _stop promptly

        # roughly matches the compute side's own lookahead (PREROLL + BUFFER);
        # with the pre-send late check below, extra depth here is harmless -
        # stale chunks are discarded cheaply rather than sent
        frame_capacity = max(1, int(fps * (PREROLL + BUFFER)))
        queue_capacity = frame_capacity * self._chunk_count
        self._out_queue: "queue.Queue[tuple[int, int, float, bytes]]" = queue.Queue(maxsize=queue_capacity)

        # Resend cache: seq -> {chunk_index: payload_bytes}, plus the seq's
        # presentation time for a quick staleness check. Bounded to
        # frame_capacity distinct frames, oldest evicted first.
        self._cache_capacity = frame_capacity
        self._cache_lock = threading.Lock()
        self._cache: "OrderedDict[int, tuple[float, dict[int, bytes]]]" = OrderedDict()

        self._stats_lock = threading.Lock()
        self._stats = {
            "queued": 0,
            "sent": 0,
            "dropped_queue_full": 0,
            "dropped_late": 0,
            "failed": 0,
            "resent": 0,
            "nak_stale": 0,
            "recv_errors": 0,
        }

        self._stop = threading.Event()
        self._sender_thread = threading.Thread(target=self._sender_loop, name=f"{name}-sender", daemon=True)
        self._nak_thread = threading.Thread(target=self._nak_loop, name=f"{name}-nak", daemon=True)
        self._sender_thread.start()
        self._nak_thread.start()

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
        """Split a frame into chunks and queue them to be sent to the device.

        Args:
            frame (np.ndarray): An (N, 3) array of uint8 RGB triples, one per pixel.
            t (float): The unix timestamp (seconds) this frame should be shown at.
        """
        payload = np.asarray(frame, dtype=np.uint8).tobytes()
        self._seq += 1
        seq = self._seq

        chunks: dict[int, bytes] = {}
        chunk_size = PIXELS_PER_CHUNK * 3
        for i in range(self._chunk_count):
            chunks[i] = payload[i * chunk_size:(i + 1) * chunk_size]

        with self._cache_lock:
            self._cache[seq] = (t, chunks)
            self._cache.move_to_end(seq)
            while len(self._cache) > self._cache_capacity:
                self._cache.popitem(last=False)

        for i, chunk_payload in chunks.items():
            self._enqueue((seq, i, t, chunk_payload))

    def _enqueue(self, item: tuple[int, int, float, bytes]):
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
                dropped_late, failed (local socket error), resent (chunks
                re-sent in response to a NAK), nak_stale (NAK for a seq no
                longer in the resend cache). Counts are per-chunk, not
                per-frame.
        """
        with self._stats_lock:
            return dict(self._stats)

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
        """Stop the sender/NAK threads and ask the device to blank its pixels."""
        self._stop.set()
        self._sender_thread.join(timeout=self.HTTP_TIMEOUT_S)
        self._nak_thread.join(timeout=self.HTTP_TIMEOUT_S)
        try:
            self._session.post(f"{self._base_url}/clear", timeout=self.HTTP_TIMEOUT_S)
        except requests.RequestException:
            pass
        self._sock.close()

    def _send_chunk(self, seq: int, chunk_index: int, t_us: int, payload: bytes):
        # chunk_count is invariant per driver (fixed by pixel_count at
        # construction) - always self._chunk_count, never per-chunk state.
        datagram = _FRAME_HEADER.pack(TYPE_FRAME, seq & 0xFFFFFFFF, t_us, chunk_index, self._chunk_count) + payload
        self._sock.send(datagram)

    def _sender_loop(self):
        # The outer except Exception is a deliberate safety net: this thread
        # runs for the life of the driver, and one bad/unexpected item must
        # never silently kill frame delivery to a fixture for good.
        while not self._stop.is_set():
            try:
                seq, chunk_index, t, payload = self._out_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                if t < time.time() - self.LATE_GRACE_S:
                    self._bump("dropped_late")
                    continue
                self._send_chunk(seq, chunk_index, int(t * 1_000_000), payload)
                self._bump("sent")
            except OSError as e:
                self._bump("failed")
                print(f"[{self.name}] failed to send frame {seq} chunk {chunk_index}: {e}")
            except Exception as e:
                self._bump("failed")
                print(f"[{self.name}] unexpected error sending frame {seq} chunk {chunk_index}: {e}")

    def _nak_loop(self):
        while not self._stop.is_set():
            try:
                datagram = self._sock.recv(_NAK.size)
            except socket.timeout:
                continue
            except OSError as e:
                self._bump("recv_errors")
                if self._stop.is_set():
                    return
                # e.g. a connected UDP socket surfaces an ICMP port-unreachable
                # (device not listening yet/restarting) as a recv() error - a
                # bare `continue` here would spin as fast as those arrive.
                print(f"[{self.name}] NAK socket error: {e}")
                time.sleep(0.05)
                continue

            try:
                if len(datagram) != _NAK.size or datagram[0] != TYPE_NAK:
                    continue
                _, seq, chunk_index = _NAK.unpack(datagram)

                with self._cache_lock:
                    entry = self._cache.get(seq)
                    payload = entry[1].get(chunk_index) if entry else None
                    t = entry[0] if entry else None

                if payload is None:
                    self._bump("nak_stale")
                    continue

                self._send_chunk(seq, chunk_index, int(t * 1_000_000), payload)
                self._bump("resent")
            except OSError as e:
                self._bump("failed")
                print(f"[{self.name}] failed to resend frame {seq} chunk {chunk_index}: {e}")
            except Exception as e:
                print(f"[{self.name}] unexpected error handling NAK: {e}")
