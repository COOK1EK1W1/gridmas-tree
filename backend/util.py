import csv
import time
import sys
from colors import tcolors, Color


def savelights(lightLocs: list[list[int]]) -> None:
    with open('tree.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(lightLocs)


def read_csv():
    with open("tree.csv") as csvfile:
        reader = csv.reader(csvfile)
        list_of_lists = [[float(item) for item in row] for row in reader]
    return list_of_lists


def create_pixels(num):
    try:
        import neopixel
        import board

        pixel_pin = board.D18
        return neopixel.NeoPixel(pixel_pin, num, auto_write=False)

    except Exception:
        print(f"{tcolors.WARNING}Cannot find neopixel module, probably because your running on a device which is not supported")
        print(f"will attempt to run in dev mode{tcolors.ENDC}\n")

        from simTree import SimTree

        return SimTree()

def pythagorasDistance(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise Exception("mismatch input size")
    total = 0
    for pair in zip(a, b):
        total += (pair[0] - pair[1]) ** 2
    return total ** 1/len(a)


def generateDistances(coords) -> list[list[float]]:
    ret = []
    for fr in coords:
        inter = []
        for to in coords:
            inter.append(pythagorasDistance(fr, to))
        ret.append(inter)
    return ret

class Tree():
    def __init__(self):

        self.coords = read_csv()

        self.num_pixels = int(len(self.coords))

        self.tree_pixels = create_pixels(self.num_pixels)

        self.height = max([x[2] for x in self.coords])

        self.distances = generateDistances(self.coords)

        self.pixels = [Color.black() for _ in range(self.num_pixels)]

        total_size = sys.getsizeof(self.distances)
        for row in self.distances:
            for element in row:
                total_size += sys.getsizeof(element)
        print("Size of the distance array in bytes:", total_size)
        
        self.last_update = time.time()


    def set_light(self, n: int, color: Color):
        self.pixels[n].set_color(color)

    def get_light(self, n: int) -> Color:
        return self.pixels[n]

    def update(self):
        for i, pixel in enumerate(self.pixels):
            self.tree_pixels[i] = pixel.toTuple()
        self.tree_pixels.show()
        sleep_time = max((1/45) - (time.time() - self.last_update), 0)
        if sleep_time == 0:
            #print("frame took too long :(")
            pass
        time.sleep(sleep_time)
        self.last_update = time.time()

    def turnOffLight(self, n: int):
        self.pixels[n].set_color(Color.black())
    
    def run(self):
        if str(type(self.tree_pixels)) == "<class 'simTree.SimTree'>":
            while True:
                self.tree_pixels.run()
        else:
            pass



tree = Tree()

if __name__ == "__main__":

    coords = read_csv()
    for pixel, coord in enumerate(coords):
        if coord[2] > 0:
            tree.pixels[pixel].set_RGB(100, 100, 100)
        else:
            tree.pixels[pixel].set_RGB(0, 0, 0)
    tree.update()
