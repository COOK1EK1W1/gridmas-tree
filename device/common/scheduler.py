"""Buffers timestamped frames and plays each one back at the moment it's due.

Runs on its own thread so strip renders never block, or are blocked by, the
WebSocket thread receiving frames in ws_server.py. Frames are held in a
min-heap keyed on presentation time - reordering isn't a concern over a
reliable, ordered WebSocket connection, but the heap's structure is kept
since a future feature may want to replace an already-buffered frame by
presentation time. See docs/docs/network-pixel-protocol.md for the wire
format.
"""

import heapq
import threading
import time
from typing import List, Optional, Protocol, Tuple

_POLL_S = 0.5  # cap on any blocking wait, so stop() is noticed promptly


class Strip(Protocol):
    pixel_count: int

    def render(self, rgb: bytes) -> None: ...
    def clear(self) -> None: ...


class FrameScheduler:
    """Owns the completed-frame buffer and the thread that plays it out.

    Submitting past capacity evicts the earliest-due slot rather than
    declining the new frame - a last-resort safety net, since the
    controller's credit-based flow control (see ws_server.py) is what's
    meant to keep the buffer from ever actually filling.

    A frame dequeued more than late_grace_s past its presentation time is
    dropped, not shown late.
    """

    def __init__(self, strip: Strip, capacity: int, late_grace_s: float = 0.2):
        self.strip = strip
        self.capacity = capacity
        self.late_grace_s = late_grace_s

        self._heap: List[Tuple[float, int, bytes]] = []

        self._cv = threading.Condition()
        self._stop = threading.Event()
        self._stats = {
            "frames_received": 0,
            "frames_shown": 0,
            "frames_dropped_late": 0,
            "frames_dropped_queue_full": 0,
            "last_frame_received_at": None,
            "last_frame_shown_at": None,
        }

        self._thread = threading.Thread(target=self._run, name="frame-scheduler", daemon=True)
        self._thread.start()

    def submit_frame(self, t: float, seq: int, payload: bytes) -> None:
        """Queue one frame for playback, evicting the earliest-due frame
        first if the buffer is already at capacity."""
        with self._cv:
            if len(self._heap) >= self.capacity:
                heapq.heappop(self._heap)
                self._stats["frames_dropped_queue_full"] += 1
            heapq.heappush(self._heap, (t, seq, payload))
            self._stats["frames_received"] += 1
            self._stats["last_frame_received_at"] = time.time()
            self._cv.notify()

    def free_slots(self) -> int:
        with self._cv:
            return self.capacity - len(self._heap)

    def depth(self) -> int:
        with self._cv:
            return len(self._heap)

    def snapshot_stats(self) -> dict:
        with self._cv:
            return dict(self._stats)

    def clear(self):
        """Drop every buffered frame and blank the strip."""
        with self._cv:
            self._heap.clear()
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
