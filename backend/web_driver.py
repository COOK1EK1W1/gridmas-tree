"""A PixelDriver for the browser (Pyodide) build of the web editor.

The desktop drivers (pygame_driver.py) render frames using the timing model in
PixelDriver.draw_and_flush_driver(): frames are computed ahead of real time and
tagged with the wall-clock time they should be shown, then displayed whenever
that time comes due. In the browser, treevis.tsx's requestAnimationFrame loop
drives frame computation itself one step at a time, so this driver just needs
to hand back whichever buffered frame is due each time it's polled - there's
no separate process pulling frames on its own schedule.

Kept in its own module (rather than pixel_driver.py) so the desktop path never
has to import it, and vice versa - pygame_driver.py fails to import under
Pyodide (no pygame/PyOpenGL there), which is exactly what GMT2025back.py uses
to fall back to this driver automatically.
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
        the newest one rather than replaying the backlog - matches
        PygamePixelDriver._play_due_frames().
        """
        now = time.time()
        while self._frame_buffer and self._frame_buffer[0][0] <= now:
            _, self._current_frame = self._frame_buffer.popleft()
        return self._current_frame
