from abc import ABC, abstractmethod
from pixel import Pixel
from multiprocessing import Queue


class PixelDriver(ABC):
    def __init__(self, queue: "Queue[list[Pixel] | None]", coords: list[tuple[float, float, float]]):
        self.queue = queue
        self.coords = coords

    @abstractmethod
    def run(self):
        ...
