from util import tree
from colors import Color
from attribute import RangeAttr, ColorAttr
import time

name = "Strip"
author = "Ciaran"


def run():
    speed = RangeAttr("speed", 0.01, 0.001, 0.1, 0.001)
    fade = RangeAttr("fade", 1.1, 1.01, 2, 0.01)
    color = ColorAttr("Color", Color.white())
    while True:
        for i in range(tree.num_pixels):
            tree.set_light(i, color.get())

            for pixel in tree.pixels:
                pixel.fade(n=fade.get())

            tree.update()
            time.sleep(speed.get())
