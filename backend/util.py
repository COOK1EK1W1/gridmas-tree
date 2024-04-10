import csv
from colors import tcolors


def savelights(lightLocs: list[list[int]]) -> None:
    with open('tree.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(lightLocs)


def read_csv():
    with open("tree.csv") as csvfile:
        reader = csv.reader(csvfile)
        list_of_lists = [[float(item) for item in row] for row in reader]
    return list_of_lists


def hsl_to_rgb(hue, sat, lit):
    """
    Convert HSL (Hue, Saturation, Lightness) to RGB (Red, Green, Blue).
    All input values should be in the range [0, 1].
    """
    if sat == 0:
        # Achromatic (gray)
        return int(lit * 255), int(lit * 255), int(lit * 255)
    else:
        def hue_to_rgb(p, q, t):
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1/6:
                return p + (q - p) * 6 * t
            if t < 1/2:
                return q
            if t < 2/3:
                return p + (q - p) * (2/3 - t) * 6
            return p

        q = lit * (1 + sat) if lit < 0.5 else lit + sat - lit * sat
        p = 2 * lit - q
        r = hue_to_rgb(p, q, hue + 1/3)
        g = hue_to_rgb(p, q, hue)
        b = hue_to_rgb(p, q, hue - 1/3)

        return int(r * 255), int(g * 255), int(b * 255)


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

    def set_light(self, n: int, colour: tuple[int, int, int] = (255, 255, 255)):
        (r, g, b) = colour
        self.pixels[n] = (g, r, b)

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
