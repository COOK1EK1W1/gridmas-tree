"""A PixelDriver for the browser (Pyodide) build of the web editor.

Unlike the network driver, the javascript paces and polls the frames itself
(via DriverRegistry.step()), so this driver only needs to hold on to the
latest frame until it's read.
"""

import numpy as np

from pixel_driver import PixelDriver


class WebPixelDriver(PixelDriver):
    """Keeps the most recently drawn frame for JS to pull and render."""

    def __init__(self, pixel_count: int, name: str):
        super().__init__(pixel_count, name)
        self._current_frame = np.zeros((pixel_count, 3))

    def flush(self, t: float):
        """Store the frame as (r, g, b) floats in 0-1 for current_frame()."""
        self._current_frame = self.pixel_buffer / 255

    def current_frame(self) -> np.ndarray:
        """The most recently drawn frame."""
        return self._current_frame
