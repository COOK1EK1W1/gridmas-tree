import neopixel
import os
import board
from dotenv import load_dotenv
import csv

load_dotenv()
pixel_pin = board.D18


class Tree():
    def __init__(self):

        envpixels = os.getenv("PIXELS")
        if envpixels == None:
            raise Exception("No env variable")
        self.num_pixels = int(envpixels)

        self.coords = read_csv()

        self.pixels = neopixel.NeoPixel(
            pixel_pin, self.num_pixels, auto_write=False)

        self.height = max([x[2] for x in self.coords])

    def set_light(self, n: int, colour: tuple[int, int, int] = (255, 255, 255)):
        self.pixels[n] = colour

    def get_light(self, n: int) -> tuple[int, int, int]:
        return self.pixels[n]

    def update(self):
        self.pixels.show()

    def turnOffLight(self, n: int):
        pixels[n] = (0, 0, 0)


def savelights(lightLocs: list[list[int]]) -> None:
    with open('bruh.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(lightLocs)


def read_csv():
    with open("bruh.csv") as csvfile:
        reader = csv.reader(csvfile)
        list_of_lists = [[float(item) for item in row] for row in reader]
    return list_of_lists


tree = Tree()


if __name__ == "__main__":

    coords = read_csv()
    for pixel, coord in enumerate(coords):
        if coord[2] > 0:
            tree.pixels[pixel] = (100, 100, 100)
        else:
            tree.pixels[pixel] = (0, 0, 0)
    tree.update()


def hsl_to_rgb(h, s, l):
    """
    Convert HSL (Hue, Saturation, Lightness) to RGB (Red, Green, Blue).
    All input values should be in the range [0, 1].
    """
    if s == 0:
        # Achromatic (gray)
        return int(l * 255), int(l * 255), int(l * 255)
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

        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)

        return int(r * 255), int(g * 255), int(b * 255)


# Example usage:
h = 0.5  # Hue (range: [0, 1])
s = 1.0  # Saturation (range: [0, 1])
l = 0.7  # Lightness (range: [0, 1])

rgb = hsl_to_rgb(h, s, l)
print(f"RGB: {rgb}")
