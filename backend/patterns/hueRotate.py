from tree import tree
from colors import Color
from attribute import RangeAttr

name = "Hue Rotate"
author = "Ciaran"


def run():
    hue = 0
    speed = RangeAttr("speed", 0.003, -0.005, 0.005, 0.0001)
    while True:
        hue = (hue + speed.get()) % 1
        for pixel in tree.pixels:
            pixel.set_color(Color.from_hsl(hue, 1, 0.5))
        tree.update()
