from abc import ABC, abstractmethod
from multiprocessing import Queue


class PixelDriver(ABC):
    def __init__(self, queue: "Queue[tuple[int, list[tuple[int, int, int]]] | None]", coords: list[tuple[float, float, float]]):
        self.queue = queue
        self.coords = coords
        self.fps = 45

    def set_fps(self, fps: int):
        self.fps = fps

    @abstractmethod
    def run(self):
        ...
