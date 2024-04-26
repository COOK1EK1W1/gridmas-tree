import csv
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


class Tree():
    def __init__(self):

        self.coords = read_csv()

        self.num_pixels = int(len(self.coords))

        self.pixels = create_pixels(self.num_pixels)

        self.height = max([x[2] for x in self.coords])

    def set_light(self, n: int, color: Color):
        self.pixels[n] = color.toTuple()

    def get_light(self, n: int) -> tuple[int, int, int]:
        (g, r, b) = self.pixels[n]
        return (r, g, b)

    def update(self):
        self.pixels.show()

    def turnOffLight(self, n: int):
        self.pixels[n] = (0, 0, 0)


tree = Tree()

if __name__ == "__main__":

    coords = read_csv()
    for pixel, coord in enumerate(coords):
        if coord[2] > 0:
            tree.pixels[pixel] = (100, 100, 100)
        else:
            tree.pixels[pixel] = (0, 0, 0)
    tree.update()
