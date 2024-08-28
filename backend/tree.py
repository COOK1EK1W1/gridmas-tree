from typing import Callable
from pixel_driver.pixel_driver import PixelDriver
from util import generate_distance_map, linear, read_tree_csv
import multiprocessing
import time
import sys
from colors import tcolors, Color, Pixel


def pick_driver() -> type[PixelDriver]:
    try:
        from pixel_driver import ws2812_tree

        return ws2812_tree.ws2812_tree

    except ImportError:
        print(f"{tcolors.WARNING}Cannot find neopixel module, probably because your running on a device which is not supported")
        print(f"will attempt to run in dev mode{tcolors.ENDC}\n")

        from pixel_driver import sim_tree
        return sim_tree.SimTree


class Tree():
    def __init__(self):
        self.fps = 45

        self.coords = read_tree_csv()

        self.num_pixels = int(len(self.coords))

        # create a 10 frame buffer to the pixel driver
        self.frame_queue: multiprocessing.Queue[tuple[int, list[int]] | None] = multiprocessing.Queue(10)

        # select the correct pixel driver for the system, either physical or sim
        driver = pick_driver()
        self.pixel_driver = driver(self.frame_queue, self.coords)

        self.height = max([x[2] for x in self.coords])

        self.distances = generate_distance_map(self.coords)

        total_size = sys.getsizeof(self.distances)
        for row in self.distances:
            for element in row:
                total_size += sys.getsizeof(element)
        print("Size of the distance array in bytes:", total_size)

        self.pixels: list[Pixel] = [Pixel((x[0], x[1], x[2])) for x in self.coords]

        self.last_update = time.perf_counter()
        self.render_times: list[float] = []

    def set_light(self, n: int, color: Color):
        self.pixels[n].set_color(color)

    def get_light(self, n: int) -> Pixel:
        return self.pixels[n]

    def update(self):
        t = time.perf_counter()
        render_time = t - self.last_update
        self.render_times.append(render_time)

        # add frame to frame queue, if frame queue is full, then this blocks until space
        self.frame_queue.put((self.fps, list(map(lambda x: x.to_int(), self.pixels))))

        if len(self.render_times) > 100:
            self.render_times.pop(0)

        if len(self.render_times) != 0:
            avgrender = sum(self.render_times) / len(self.render_times)

            if avgrender != 0:
                print(f"render: {str(avgrender*1000)[0:5]}ms ps: {round((avgrender / (1/tree.fps))*100, 2)}%       ", end="\r")
        self.last_update = time.perf_counter()

    def set_fps(self, fps: int):
        self.fps = fps
        self.update()

    def run(self):
        process = multiprocessing.Process(target=self.pixel_driver.run, args=())
        print("running the processs")
        process.start()

    def fade(self, n: float = 1.1):
        for pixel in self.pixels:
            pixel.fade(n)

    def black(self):
        """Set all the pixels of the tree to black"""
        for pixel in self.pixels:
            pixel.set_rgb(0, 0, 0)

    def fill(self, color: Color):
        for pixel in self.pixels:
            pixel.set_color(color)

    def lerp(self, color: Color, frames: int, fn: Callable[[float], float] = linear):
        for pixel in self.pixels:
            pixel.lerp(color.to_tuple(), frames, fn=fn)

    def sleep(self, frames: int, allow_lerp: bool = False):
        for _ in range(frames):
            if allow_lerp:
                for pixel in tree.pixels:
                    pixel.cont_lerp()
            self.update()


tree = Tree()
