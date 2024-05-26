from tree import tree
import random
from colors import Color
from attribute import ColorAttr

name = "Twinkle"
author = "Ciaran"


def run():
    baseColor = ColorAttr("color", Color(120, 20, 0))
    while True:
        x = random.randint(0, tree.num_pixels - 1)

        tree.set_light(x, baseColor.get())

        for pixel in tree.pixels:
            r, g, b = pixel.toTuple()
            pixel.set_RGB(min(int(r + 5), 200), min(int(g + 5), 55), min(1, int(b + 5)))

        tree.update()
