from abc import ABC, abstractmethod
from typing import Callable
import numpy as np
from dataclasses import dataclass
import time

from fixture import Fixture


PREROLL = 1
BUFFER = 1

class PixelDriver(ABC):

    def __init__(self, pixel_count: int, name: str, fps: int):
        self.fixtures: list[tuple[Fixture, int]] = []
        self.pixel_count = pixel_count
        self.pixel_buffer = np.zeros((pixel_count, 3))
        self.last_frame_time = 0
        self.fps = fps
        self.name = name

    def add_fixture(self, f: Fixture, index: int):
        self.fixtures.append((f, index))
        len(f.pixels())

    def draw_and_flush_driver(self):
        now = time.time()
        needs_frame = self.last_frame_time < (now + PREROLL + BUFFER)
        if needs_frame:
            if self.last_frame_time == 0:
                self.last_frame_time = now + 1
            else:
                self.last_frame_time += 1 / self.fps
            for (fixture, offset) in self.fixtures:
                print(fixture)
                if fixture.draw_fn is not None:
                    fixture.draw_fn()
                    frame = fixture._request_frame()
                    self.flush(frame, self.last_frame_time)
            print(f"{self.name} frame for {self.last_frame_time}, generated at {time.time()}")


    @abstractmethod
    def flush(self, frame, t: float):
        ...

    def update_draw(self, draw_fn: Callable):
        for fixture, _ in self.fixtures: 
            fixture.draw_fn = draw_fn


class NetworkPixelDriver(PixelDriver):
    def __init__(self, address: str, pixel_count: int, name: str, fps: int):
        super().__init__(pixel_count, name, fps)
        self._address = address

    def flush(self, frame, t: float):
        for fixture, offset in self.fixtures:
            for pixel in frame:
                print(f"({pixel.r}, {pixel.g}, {pixel.b}) ", end="")
            print()



class DriverRegistry:
    def __init__(self):
        self._registry: list[PixelDriver] = []

    def draw_and_flush_drivers(self):
        for driver in self._registry:
            driver.draw_and_flush_driver()

    def update_draw(self, draw_fn: Callable):
        for driver in self._registry:
            driver.update_draw(draw_fn)

    def clear(self):
        self._registry = []

    def register(self, driver: PixelDriver):
        self._registry.append(driver)

driver_registry = DriverRegistry()
