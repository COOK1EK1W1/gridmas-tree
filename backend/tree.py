from pixel_driver.pixel_driver import PixelDriver
from util import generate_distance_map, read_tree_csv
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

        self.frame_queue: multiprocessing.Queue[tuple[int, list[int]] | None] = multiprocessing.Queue()
        driver = pick_driver()
        self.pixel_driver = driver(self.frame_queue, self.coords)

        self.height = max([x[2] for x in self.coords])

        self.distances = generate_distance_map([[y for y in x] for x in self.coords])

        total_size = sys.getsizeof(self.distances)
        for row in self.distances:
            for element in row:
                total_size += sys.getsizeof(element)
        print("Size of the distance array in bytes:", total_size)

        self.pixels: list[Pixel] = [Pixel((x[0], x[1], x[2])) for x in self.coords]

        self.last_update = time.perf_counter()

        self.render_times: list[float] = []
        self.sleep_times: list[float] = []

    def set_light(self, n: int, color: Color):
        self.pixels[n].set_color(color)

    def get_light(self, n: int) -> Pixel:
        return self.pixels[n]

    def update(self):
        rt = time.perf_counter()
        self.frame_queue.put((self.fps, list(map(lambda x: x.to_int(), self.pixels))))

        render_time = rt - self.last_update
        sleep_time = (1 / self.fps) - render_time

        try:
            buffer_size = self.frame_queue.qsize()

            if buffer_size > 4:
                time.sleep(max(sleep_time, 0))
            if buffer_size > 10:
                time.sleep((1 / self.fps))
        except NotImplementedError:
            time.sleep(max(sleep_time, 0))

        self.sleep_times.append(sleep_time)
        self.render_times.append(render_time)

        if len(self.render_times) > 100:
            self.sleep_times.pop(0)
            self.render_times.pop(0)

        if len(self.sleep_times) != 0 and len(self.render_times) != 0:
            avgsleep = sum(self.sleep_times) / len(self.sleep_times)
            avgrender = sum(self.render_times) / len(self.render_times)

            avg_min_sleep = sum(map(lambda x: max(0, x), self.sleep_times)) / len(self.sleep_times)

            fps = 1 / (avgrender + avg_min_sleep)
            if avgrender != 0 and avgsleep != 0:
                print(f"render: {round(avgrender, 5)} sleep: {round(avgsleep, 4)} ps: {round((avgrender / (avgsleep + avgrender))*100, 2)}% fps: {round(fps, 1)}         ", end="\r")
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


tree = Tree()
