"""Buffers timestamped frames and plays each one back at the moment it's due.

Runs on its own thread so strip renders never block, or are blocked by, the
UDP thread receiving frame chunks in udp_frame.py. Frames are held in a
min-heap keyed on presentation time, since datagrams can arrive out of
order. See docs/docs/network-pixel-protocol.md for the wire format this
reassembles and the gap-detection/retransmission scheme this implements.
"""

import heapq
import threading
import time
from typing import Dict, List, Optional, Protocol, Tuple

_POLL_S = 0.5  # cap on any blocking wait, so stop() is noticed promptly

STALL_AFTER = 3  # frames: see docs/docs/network-pixel-protocol.md "Gap detection"


class Strip(Protocol):
    pixel_count: int

    def render(self, rgb: bytes) -> None: ...
    def clear(self) -> None: ...


class _PendingFrame:
    """A frame that hasn't had all its chunks arrive yet."""

    __slots__ = ("t", "seq", "chunk_count", "chunks", "naked", "stall_count")

    def __init__(self, t: float, seq: int, chunk_count: int):
        self.t = t
        self.seq = seq
        self.chunk_count = chunk_count
        self.chunks: Dict[int, bytes] = {}
        self.naked: set = set()  # chunk indices a NAK has already been sent for
        self.stall_count = 0  # later frames completed while this one is still pending

    def is_complete(self) -> bool:
        return len(self.chunks) == self.chunk_count

    def assemble(self) -> bytes:
        return b"".join(self.chunks[i] for i in range(self.chunk_count))

    def missing_chunks(self) -> List[int]:
        return [i for i in range(self.chunk_count) if i not in self.chunks]


class FrameScheduler:
    """Owns the pending/completed-frame buffers and the thread that plays
    completed frames out.

    capacity caps both the completed-frame heap and the pending (still
    being reassembled) frames, each independently - a gap that wouldn't fit
    in the buffer anyway is moot, per docs/docs/network-pixel-protocol.md.
    Submitting past capacity evicts the earliest-due slot rather than
    declining the new frame/chunk (this device type never rejects - there's
    no response channel to reject over on UDP anyway).

    A frame dequeued more than late_grace_s past its presentation time is
    dropped, not shown late.
    """

    def __init__(self, strip: Strip, capacity: int, late_grace_s: float = 0.2, stall_after: int = STALL_AFTER):
        self.strip = strip
        self.capacity = capacity
        self.late_grace_s = late_grace_s
        self.stall_after = stall_after

        self._heap: List[Tuple[float, int, bytes]] = []
        self._pending: Dict[int, _PendingFrame] = {}
        self._nak_queue: List[Tuple[int, int]] = []  # (seq, chunk_index) ready to be NAK'd

        self._cv = threading.Condition()
        self._stop = threading.Event()
        self._stats = {
            "frames_received": 0,
            "frames_shown": 0,
            "frames_dropped_late": 0,
            "frames_dropped_queue_full": 0,
            "naks_sent": 0,
            "chunks_rejected": 0,
            "last_frame_received_at": None,
            "last_frame_shown_at": None,
        }

        self._thread = threading.Thread(target=self._run, name="frame-scheduler", daemon=True)
        self._thread.start()

    def submit_chunk(self, t: float, seq: int, chunk_index: int, chunk_count: int, payload: bytes) -> None:
        """Queue one chunk of a frame. Once every chunk of `seq` has
        arrived, the reassembled frame is pushed onto the completed-frame
        heap (evicting the earliest-due completed frame first if the heap
        is already at capacity)."""
        with self._cv:
            if chunk_count <= 0 or not (0 <= chunk_index < chunk_count):
                self._stats["chunks_rejected"] += 1
                return

            pending = self._pending.get(seq)
            if pending is None:
                if len(self._pending) >= self.capacity:
                    self._evict_earliest_pending_locked()
                pending = _PendingFrame(t, seq, chunk_count)
                self._pending[seq] = pending
            elif chunk_count != pending.chunk_count:
                self._stats["chunks_rejected"] += 1
                return  # inconsistent chunk_count for an already-pending seq - ignore

            if chunk_index in pending.chunks:
                return  # duplicate chunk - idempotent, ignore
            pending.chunks[chunk_index] = payload

            if not pending.is_complete():
                return

            del self._pending[seq]
            self._complete_frame_locked(pending)

    def _complete_frame_locked(self, pending: "_PendingFrame") -> None:
        payload = pending.assemble()

        if len(self._heap) >= self.capacity:
            self._evict_earliest_heap_locked()
        heapq.heappush(self._heap, (pending.t, pending.seq, payload))
        self._stats["frames_received"] += 1
        self._stats["last_frame_received_at"] = time.time()

        # Bump stall_count for every still-pending frame that's earlier than
        # this one - it just got "another later frame arrived" evidence.
        for other_seq, other in list(self._pending.items()):
            if other_seq >= pending.seq:
                continue
            other.stall_count += 1
            if other.stall_count >= self.stall_after:
                for idx in other.missing_chunks():
                    if idx not in other.naked:
                        other.naked.add(idx)
                        self._nak_queue.append((other_seq, idx))
                        self._stats["naks_sent"] += 1

        self._cv.notify()

    def _evict_earliest_heap_locked(self):
        if self._heap:
            heapq.heappop(self._heap)
            self._stats["frames_dropped_queue_full"] += 1

    def _evict_earliest_pending_locked(self):
        if not self._pending:
            return
        oldest_seq = min(self._pending, key=lambda s: self._pending[s].t)
        del self._pending[oldest_seq]
        self._stats["frames_dropped_queue_full"] += 1

    def collect_naks(self) -> List[Tuple[int, int]]:
        """Pop and return every (seq, chunk_index) that's become due for a
        NAK since the last call. Called from udp_frame.py's receive loop."""
        with self._cv:
            if not self._nak_queue:
                return []
            naks, self._nak_queue = self._nak_queue, []
            return naks

    def depth(self) -> int:
        with self._cv:
            return len(self._heap)

    def snapshot_stats(self) -> dict:
        with self._cv:
            return dict(self._stats)

    def clear(self):
        """Drop every buffered/pending frame and blank the strip."""
        with self._cv:
            self._heap.clear()
            self._pending.clear()
            self._nak_queue.clear()
            self._cv.notify_all()
        self.strip.clear()

    def stop(self):
        self._stop.set()
        with self._cv:
            self._cv.notify_all()
        self._thread.join(timeout=1)

    def _run(self):
        while not self._stop.is_set():
            due = self._take_due_frame()
            if due is None:
                continue
            t, payload = due
            if time.time() - t > self.late_grace_s:
                with self._cv:
                    self._stats["frames_dropped_late"] += 1
                continue
            try:
                self.strip.render(payload)
            except Exception as e:  # a bad frame must not kill the playback thread
                print(f"frame-scheduler: render failed: {e}")
                continue
            with self._cv:
                self._stats["frames_shown"] += 1
                self._stats["last_frame_shown_at"] = time.time()

    def _take_due_frame(self) -> Optional[Tuple[float, bytes]]:
        """Pop (t, payload) for the earliest completed frame that is due
        now. Returns None if the heap is empty or its next frame isn't due
        yet, having first waited (up to _POLL_S) for that to change."""
        with self._cv:
            if not self._heap:
                self._cv.wait(_POLL_S)
                return None
            t, _seq, payload = self._heap[0]
            delay = t - time.time()
            if delay > 0:
                self._cv.wait(min(delay, _POLL_S))
                return None
            heapq.heappop(self._heap)
            return t, payload
