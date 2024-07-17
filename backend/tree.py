from util import generate_distance_map, read_tree_csv
from pixel import Pixel
import time
import sys
from colors import tcolors, Color


def create_pixels(num: int):
    try:
        import neopixel
        import board

        pixel_pin = board.D18
        return neopixel.NeoPixel(pixel_pin, num, auto_write=False, pixel_order="RGB")

    except Exception:
        print(f"{tcolors.WARNING}Cannot find neopixel module, probably because your running on a device which is not supported")
        print(f"will attempt to run in dev mode{tcolors.ENDC}\n")

        from simTree import SimTree

        return SimTree()


class Tree():
    def __init__(self):

        self.coords = read_tree_csv()

        self.num_pixels = int(len(self.coords))

        self.tree_pixels = create_pixels(self.num_pixels)

        self.height = max([x[2] for x in self.coords])

        self.distances = generate_distance_map([[y for y in x] for x in self.coords])

        self.pixels: list[Pixel] = []
        for x in self.coords:
            self.pixels.append(Pixel((x[0], x[1], x[2])))
        print(len(self.pixels))

        total_size = sys.getsizeof(self.distances)
        for row in self.distances:
            for element in row:
                total_size += sys.getsizeof(element)
        print("Size of the distance array in bytes:", total_size)

        self.last_update = time.perf_counter()

        self.frame_times: list[float] = []
        self.sleep_times: list[float] = []

    def set_light(self, n: int, color: Color):
        self.pixels[n].set_color(color)

    def get_light(self, n: int) -> Pixel:
        return self.pixels[n]

    def update(self):
        for i, pixel in enumerate(self.pixels):
            self.tree_pixels[i] = pixel.toTuple()
        self.tree_pixels.show()

        frame_time = time.perf_counter() - self.last_update
        sleep_time = max((1 / 45) - frame_time, 0)
        if sleep_time == 0:
            # print("frame took too long :(")
            pass
        self.frame_times.append(frame_time)
        self.sleep_times.append(sleep_time)
        if len(self.frame_times) > 100:
            self.frame_times.pop(0)
            self.sleep_times.pop(0)
        if len(self.frame_times) != 0 and len(self.sleep_times) != 0:
            avgframe = sum(self.frame_times) / len(self.frame_times)
            avgsleep = sum(self.sleep_times) / len(self.sleep_times)
            fps = 1 / (avgframe + avgsleep)
            if avgframe != 0 and avgsleep != 0:
                print(f"ft: {round(avgframe, 4)} st: {round(avgsleep, 4)} ps: {round((avgframe / (avgsleep + avgframe))*100, 2)}% fps: {round(fps, 1)}         ", end="\r")
        time.sleep(sleep_time)
        self.last_update = time.perf_counter()

    def turnOffLight(self, n: int):
        self.pixels[n].set_color(Color.black())

    def run(self):
        if str(type(self.tree_pixels)) == "<class 'simTree.SimTree'>":
            self.tree_pixels.run()
            return True
        else:
            pass

    def fade(self, n: float = 1.1):
        for pixel in self.pixels:
            pixel.fade(n)

    def black(self):
        for pixel in self.pixels:
            pixel.set_RGB(0, 0, 0)


tree = Tree()
