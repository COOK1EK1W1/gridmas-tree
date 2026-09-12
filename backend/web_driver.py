"""A PixelDriver for the browser (Pyodide) build of the web editor.

Unlike the network driver, the javascript polls the frames directly,
so this driver only needs to hand back frame when it's polled.
"""

import time
from collections import deque

import numpy as np

from pixel_driver import PixelDriver


class WebPixelDriver(PixelDriver):
    """Buffers frames tagged with a presentation time for JS to pull and render."""

    def __init__(self, pixel_count: int, name: str, fps: int):
        super().__init__(pixel_count, name, fps)
        self._frame_buffer: deque[tuple[float, np.ndarray]] = deque()
        self._current_frame = np.zeros(pixel_count, dtype=np.uint32)

    def flush(self, frame: np.ndarray, t: float):
        """Buffer a frame of (r, g, b) triples, packed into GRB ints, for pop_due_frame()."""
        r = frame[:, 0].astype(np.uint32)
        g = frame[:, 1].astype(np.uint32)
        b = frame[:, 2].astype(np.uint32)
        packed = (r << 8) | (g << 16) | b
        self._frame_buffer.append((t, packed))

    def pop_due_frame(self) -> np.ndarray:
        """Advance to the newest buffered frame that is now due, and return it.

        If several frames have become due since the last poll, skip straight to
        the newest one rather than replaying the backlog.
        """
        now = time.time()
        while self._frame_buffer and self._frame_buffer[0][0] <= now:
            _, self._current_frame = self._frame_buffer.popleft()
        return self._current_frame
