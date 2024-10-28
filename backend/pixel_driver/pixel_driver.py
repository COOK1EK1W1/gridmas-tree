from abc import ABC, abstractmethod
import queue
import time
from multiprocessing import Queue


class PixelDriver(ABC):
    def __init__(self, queue: "Queue[tuple[int, list[int]] | None]", coords: list[tuple[float, float, float]]):
        self.queue = queue
        self.coords = coords

    def clear_queue(self):
        while not self.queue.empty():
            self.queue.get()

    def run(self):
        cur_fps = 45
        start_time = time.perf_counter()

        while True:
            try:
                data = self.queue.get(timeout=0.04)
                if data is None:
                    continue
                fps, framea = data
                if fps != cur_fps:
                    cur_fps = fps
                self.draw(framea)

                time.sleep((1 / fps) - (time.perf_counter() - start_time) % (1 / fps))

            except queue.Empty:
                pass



            self.show()

    @abstractmethod
    def draw(self, frame: list[int]):
        ...

    @abstractmethod
    def show(self):
        ...
