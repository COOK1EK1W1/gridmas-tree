from attribute import RangeAttr
from tree import tree
import time

name = "RGB"
author = "Ciaran"


def draw():
    sleep_time = RangeAttr("sleep time", 1, 0.1, 3, 0.1)

    offset = 0
    while True:
        offset = (offset + 1) % 3

        for i, pixel in enumerate(tree.pixels):
            r = 255 if (i + offset) % 3 == 0 else 0
            g = 255 if (i + offset) % 3 == 1 else 0
            b = 255 if (i + offset) % 3 == 2 else 0
            pixel.set_rgb(r, g, b)
        yield
        time.sleep(sleep_time.get())
