from abc import ABC, abstractmethod
from re import Pattern
from typing import Callable, Generator, Literal, Optional
import numpy as np
import time

from numpy import ndarray

from fixture import Fixture, setActiveFixture


PREROLL = 0.2
BUFFER = 0.2

class PixelDriver(ABC):

    def __init__(self, pixel_count: int, name: str, fps: int):
        self.fixtures: list[tuple[Fixture, int]] = []
        self.pixel_count = pixel_count
        self.pixel_buffer = np.zeros((pixel_count, 3))
        self.last_frame_time = 0
        self.fps = fps
        self.name = name

        # once-a-second effective-fps log, so the compute rate is visible
        # without a print() on every single frame
        self._frames_since_log = 0
        self._last_log_at = time.time()

    def add_fixture(self, f: Fixture, index: int):
        self.fixtures.append((f, index))
        len(f._pixels)

    def draw_and_flush_driver(self) -> bool:
        """Generate and flush one frame if the lookahead horizon calls for it.

        Returns:
            bool: True if a frame was generated this call, False if we're
                already computed far enough ahead of real time. The caller uses
                this to decide whether to sleep - spinning here would starve the
                driver's own network sender threads of the GIL.
        """
        now = time.time()
        needs_frame = self.last_frame_time < (now + PREROLL + BUFFER)
        if not needs_frame:
            return False

        if self.last_frame_time == 0:
            self.last_frame_time = now + 1
        else:
            self.last_frame_time += 1 / self.fps
        for fixture, _ in self.fixtures:
            if fixture.draw_fn is not None:
                setActiveFixture(fixture)
                fixture.draw_fn()
                frame = fixture._request_frame()
                self.flush(frame, self.last_frame_time)
        setActiveFixture(None)

        self._frames_since_log += 1
        elapsed = now - self._last_log_at
        if elapsed >= 1.0:
            print(f"[{self.name}] generating {self._frames_since_log / elapsed:.1f} fps")
            self._frames_since_log = 0
            self._last_log_at = now
        return True


    @abstractmethod
    def flush(self, frame: ndarray[tuple[int, Literal[3]], np.dtype[np.unsignedinteger]], t: float):
        ...

    def update_draw(self, draw_fn: Callable[[], Optional[Generator[None, None, None]]]):
        for fixture, _ in self.fixtures: 
            fixture.draw_fn = draw_fn

    def close(self):
        """Release anything this driver owns (sockets, threads).

        A no-op for drivers that hold no resources; NetworkPixelDriver
        overrides it. Called when a display is torn down - see
        DriverRegistry.clear().
        """


class DriverRegistry:
    def __init__(self):
        self._registry: list[PixelDriver] = []
        self.last_print = 0

    def draw_and_flush_drivers(self) -> bool:
        """Returns True if any driver generated a frame this call."""
        produced = False
        if len(self._registry) == 0 and time.time() > self.last_print + 1:
            print("No drivers found")
            self.last_print = time.time()
        for driver in self._registry:
            produced |= driver.draw_and_flush_driver()
        return produced

    def update_draw(self, draw_fn: Callable[[], Optional[Generator[None, None, None]]]):
        for driver in self._registry:
            driver.update_draw(draw_fn)

    def clear(self):
        """Drop every registered driver, closing each one first.

        Closing is the point: a NetworkPixelDriver owns a connection thread
        that keeps reconnecting for the life of the object, and a device
        serves one controller at a time. A driver that were merely dropped
        would go on fighting its own replacement for that single slot -
        each new connection tearing down the other's.
        """
        for driver in self._registry:
            try:
                driver.close()
            except Exception as e:
                print(f"[{driver.name}] error while closing: {e}")
        self._registry = []

    def register(self, driver: PixelDriver):
        self._registry.append(driver)

driver_registry = DriverRegistry()
