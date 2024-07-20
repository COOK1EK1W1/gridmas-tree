from abc import ABC, abstractmethod
from multiprocessing import Queue


class PixelDriver(ABC):
    def __init__(self, queue: "Queue[list[tuple[int, int, int]] | None]", coords: list[tuple[float, float, float]]):
        self.queue = queue
        self.coords = coords

    @abstractmethod
    def run(self):
        ...
