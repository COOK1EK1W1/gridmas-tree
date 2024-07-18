from pixel_driver.pixel_driver import PixelDriver
from util import generate_distance_map, read_tree_csv
import multiprocessing
from pixel import Pixel
import time
import sys
from colors import tcolors, Color


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

        self.coords = read_tree_csv()

        self.num_pixels = int(len(self.coords))

        self.frame_queue: multiprocessing.Queue[list[Pixel] | None] = multiprocessing.Queue()
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

        self.frame_times: list[float] = []
        self.draw_times: list[float] = []
        self.render_times: list[float] = []
        self.sleep_times: list[float] = []

    def set_light(self, n: int, color: Color):
        self.pixels[n].set_color(color)

    def get_light(self, n: int) -> Pixel:
        return self.pixels[n]

    def update(self):
        rt = time.perf_counter()
        if self.frame_queue.empty():
            self.frame_queue.put(self.pixels)
        dt = time.perf_counter()

        render_time = rt - self.last_update
        draw_time = dt - rt
        frame_time = dt - self.last_update
        sleep_time = (1 / 45) - frame_time

        self.frame_times.append(frame_time)
        self.sleep_times.append(sleep_time)
        self.render_times.append(render_time)
        self.draw_times.append(draw_time)

        if len(self.frame_times) > 100:
            self.frame_times.pop(0)
            self.sleep_times.pop(0)
            self.draw_times.pop(0)
            self.render_times.pop(0)

        if len(self.frame_times) != 0 and len(self.sleep_times) != 0 and len(self.draw_times) != 0 and len(self.render_times) != 0:
            avgframe = sum(self.frame_times) / len(self.frame_times)
            avgsleep = sum(self.sleep_times) / len(self.sleep_times)
            avgdraw = sum(self.draw_times) / len(self.draw_times)
            avgrender = sum(self.render_times) / len(self.render_times)

            avg_min_sleep = sum(map(lambda x: max(0, x), self.sleep_times)) / len(self.sleep_times)

            fps = 1 / (avgframe + avg_min_sleep)
            if avgframe != 0 and avgsleep != 0:
                print(f"render: {round(avgrender, 5)} draw: {round(avgdraw, 5)} total: {round(avgframe, 4)} sleep: {round(avgsleep, 4)} ps: {round((avgframe / (avgsleep + avgframe))*100, 2)}% fps: {round(fps, 1)}         ", end="\r")
        time.sleep(max(sleep_time, 0))
        self.last_update = time.perf_counter()

    def turnOffLight(self, n: int):
        self.pixels[n].set_color(Color.black())

    def run(self):
        process = multiprocessing.Process(target=self.pixel_driver.run, args=())
        process.start()

    def fade(self, n: float = 1.1):
        for pixel in self.pixels:
            pixel.fade(n)

    def black(self):
        for pixel in self.pixels:
            pixel.set_RGB(0, 0, 0)


tree = Tree()
