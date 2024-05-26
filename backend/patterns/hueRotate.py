from tree import tree
from colors import Color
from attribute import RangeAttr

name = "Hue Rotate"
author = "Ciaran"


def run():
    hue = 0
    speed = RangeAttr("speed", 0.02, 0.01, 0.1, 0.01)
    while True:
        hue = (hue + speed.get()) % 1
        for pixel in tree.pixels:
            pixel.set_color(Color.fromHSL(hue, 1, 0.5))
        tree.update()
