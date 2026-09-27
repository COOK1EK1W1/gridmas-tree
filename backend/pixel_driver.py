from abc import ABC, abstractmethod
from typing import Literal
import numpy as np
import time
from fixture import Fixture

# the pattern is running this far ahead of future
PREROLL = 0.1
# add extra buffer past preroll
BUFFER = 0.1

class PixelDriver(ABC):

    def __init__(self, pixel_count: int, name: str, fps: int):
        self.fixtures: list[tuple[Fixture, int]] = []
        self.pixel_count = pixel_count
        self.pixel_buffer = np.zeros((pixel_count, 3))
        self.last_frame_time = 0
        self.fps = fps
        self.name = name

        # logging variables
        self._frames_since_log = 0
        self._last_log_at = 0

    def add_fixture(self, new_fixture: Fixture, index: int):
        """ Add a fixture to registry, with index offset into pixel strip. 
        ValueError if overlapping pixels with another fixture"""
        new_start = index
        new_end = index + len(new_fixture._pixels)
        for fixture, start in self.fixtures:
            end = start + len(fixture._pixels)
            if new_start < end and start < new_end:
                raise ValueError(
                f"LEDs {new_start}-{new_end - 1} overlap an existing "
                f"fixture at {start}-{end - 1}"
            )
        self.fixtures.append((new_fixture, index))

    def draw_and_flush_driver(self) -> bool:
        """Generate and flush one frame if the lookahead horizon calls for it.

        Returns:
            bool: True if a frame was generated this call, False if we're
                already computed far enough ahead of real time.
        """
        now = time.time()
        needs_frame = self.last_frame_time < (now + PREROLL + BUFFER)
        if not needs_frame:
            return False

        if self.last_frame_time == 0:
            self.last_frame_time = now + PREROLL
        else:
            self.last_frame_time += 1 / self.fps
        self._draw_fixtures(self.last_frame_time)

        self._frames_since_log += 1
        elapsed = now - self._last_log_at
        if elapsed >= 1.0:
            print(f"[{self.name}] generating {self._frames_since_log / elapsed:.1f} fps")
            self._frames_since_log = 0
            self._last_log_at = now
        return True


    def _draw_fixtures(self, t: float):
        for fixture, offset in self.fixtures:
            if fixture._draw_fn is not None:
                self.pixel_buffer[offset:] = fixture._request_frame()
        self.flush(t)

    @abstractmethod
    def flush(self, t: float):
        """Send the self.pixel_buffer to the device for display at time t"""

    def close(self):
        """Release anything this driver owns (sockets, threads). 
        A no-op for drivers that hold no resources"""


class DriverRegistry:
    def __init__(self):
        self._registry: list[PixelDriver] = []
        self.last_print = 0

    def draw_and_flush_drivers(self) -> bool:
        """Returns True if any driver generated a frame this call."""
        produced = False
        now = time.time()
        if len(self._registry) == 0 and now > self.last_print + 1:
            print("No drivers found")
            self.last_print = now
        for driver in self._registry:
            produced |= driver.draw_and_flush_driver()
        return produced

    def clear(self):
        """Drop every registered driver, closing each one first"""
        for driver in self._registry:
            try:
                driver.close()
            except Exception as e:
                print(f"[{driver.name}] error while closing: {e}")
        self._registry = []

    def register(self, driver: PixelDriver):
        self._registry.append(driver)

driver_registry = DriverRegistry()
