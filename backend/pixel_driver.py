from abc import ABC, abstractmethod
from typing import Callable, Optional
import math
import numpy as np
import time
from fixture import Clock, Fixture, set_active_clock

# the pattern is running this far ahead of future
PREROLL = 1
# add extra buffer past preroll
BUFFER = 0.1
# display_update() is called at this rate on the presentation timeline
DISPLAY_TICK_FPS = 45

class PixelDriver(ABC):

    def __init__(self, pixel_count: int, name: str):
        self.fixtures: list[tuple[Fixture, int]] = []
        self.pixel_count = pixel_count
        self.pixel_buffer = np.zeros((pixel_count, 3))
        self.fps = 45
        self.name = name

        # frame n since the base is displayed at _base_time + n / _base_fps,
        # rebased whenever the fps changes so float error doesn't accumulate
        self._base_time: Optional[float] = None
        self._base_fps = 45
        self._frames_since_base = 0

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

    def start(self, t0: float, now: float):
        """Put this driver's frames on the grid t0 + n / fps.

        A driver started after the show is already running skips ahead to the
        first slot on that grid it can still get to the device in time.
        """
        n = 0
        if t0 < now + PREROLL:
            n = math.ceil((now + PREROLL - t0) * self.fps)
        self._base_time = t0 + n / self.fps
        self._base_fps = self.fps
        self._frames_since_base = 0

    def next_frame_time(self) -> Optional[float]:
        """The unix time the next frame will be displayed at, None if not started"""
        if self._base_time is None:
            return None
        return self._base_time + self._frames_since_base / self._base_fps

    def needs_frame(self, now: float) -> bool:
        """True if the next frame falls inside the lookahead horizon"""
        t = self.next_frame_time()
        return t is not None and t < now + PREROLL + BUFFER

    def draw_next_frame(self) -> float:
        """Generate and flush the next frame, returning the time it will be displayed at"""
        t = self.next_frame_time()
        assert t is not None, f"[{self.name}] drawn before start()"
        self._draw_fixtures(t)

        self._frames_since_base += 1
        if self.fps != self._base_fps:
            # set_fps() was called during this frame, the next frame is 1/new fps away
            self._base_time = t + 1 / self.fps
            self._base_fps = self.fps
            self._frames_since_base = 0

        self._frames_since_log += 1
        now = time.time()
        elapsed = now - self._last_log_at
        if elapsed >= 1.0:
            print(f"[{self.name}] generating {self._frames_since_log / elapsed:.1f} fps")
            self._frames_since_log = 0
            self._last_log_at = now
        return t


    def _draw_fixtures(self, t: float):
        for fixture, offset in self.fixtures:
            if fixture._draw_fn is not None:
                self.pixel_buffer[offset:] = fixture._request_frame(t)
                self.fps = fixture._fps
        self.flush(t)

    @abstractmethod
    def flush(self, t: float):
        """Send the self.pixel_buffer to the device for display at time t"""

    def close(self):
        """Release anything this driver owns (sockets, threads). 
        A no-op for drivers that hold no resources"""


class DriverRegistry:
    """Every driver in the running show, all timed from one shared epoch T0.

    Frame n of a driver is displayed at T0 + n / fps, and display_update() is
    called at T0 + k / DISPLAY_TICK_FPS, always before any frame displayed at or
    after that tick is drawn. Music started at T0 therefore lines up with frame 0.
    """

    def __init__(self):
        self._registry: list[PixelDriver] = []
        self.last_print = 0

        self.t0: Optional[float] = None
        self._display_update: Optional[Callable[[], None]] = None
        self._display_clock = Clock()

    def start(self, display_update: Optional[Callable[[], None]] = None) -> float:
        """Begin the show start_lead seconds from now.

        Returns:
            float: T0, the unix time the first frame is displayed at
        """
        now = time.time()
        self.t0 = now + PREROLL
        self._display_update = display_update
        self._display_clock.reset()
        for driver in self._registry:
            driver.start(self.t0, now)
        return self.t0

    def _next_tick_time(self) -> float:
        assert self.t0 is not None
        return self.t0 + self._display_clock.frame / DISPLAY_TICK_FPS

    def _run_display_ticks(self, t: float):
        """Run every display_update() tick due at or before the frame displayed at t"""
        if self._display_update is None or self.t0 is None:
            return
        while (tick := self._next_tick_time()) <= t + 1e-9:
            self._display_clock.begin_frame(tick)
            set_active_clock(self._display_clock)
            try:
                self._display_update()
            finally:
                set_active_clock(None)
                self._display_clock.end_frame()

    def draw_and_flush_drivers(self) -> bool:
        """Draw the earliest frame that falls inside the lookahead horizon.

        Returns True if a frame was generated this call."""
        now = time.time()
        if len(self._registry) == 0 and now > self.last_print + 1:
            print("No drivers found")
            self.last_print = now

        due = [driver for driver in self._registry if driver.needs_frame(now)]
        if not due:
            return False
        driver = min(due, key=lambda d: d.next_frame_time())
        self._run_display_ticks(driver.next_frame_time())
        driver.draw_next_frame()
        return True

    def step(self) -> Optional[PixelDriver]:
        """Draw the earliest next frame straight away, ignoring the wall clock.

        Used by the web editor, which paces frames itself.

        Returns:
            The driver that drew a frame, or None if nothing is started.
        """
        started = [driver for driver in self._registry if driver.next_frame_time() is not None]
        if not started:
            return None
        driver = min(started, key=lambda d: d.next_frame_time())
        self._run_display_ticks(driver.next_frame_time())
        driver.draw_next_frame()
        return driver

    def clear(self):
        """Drop every registered driver, closing each one first, and end the show"""
        for driver in self._registry:
            try:
                driver.close()
            except Exception as e:
                print(f"[{driver.name}] error while closing: {e}")
        self._registry = []
        self.t0 = None
        self._display_update = None

    def register(self, driver: PixelDriver):
        self._registry.append(driver)
        if self.t0 is not None:
            driver.start(self.t0, time.time())

driver_registry = DriverRegistry()
