from tree import tree
from colors import Color
from attribute import RangeAttr, ColorAttr

name = "Strip"
author = "Ciaran"


def run():
    tree.fps = 75
    fade = RangeAttr("fade", 1.1, 1.01, 2, 0.01)
    color = ColorAttr("Color", Color.white())
    while True:
        for pixel in tree.pixels:
            pixel.set_color(color.get())

            for pixel in tree.pixels:
                pixel.fade(n=fade.get())

            tree.update()
