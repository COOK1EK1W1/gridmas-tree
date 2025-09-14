from gridmas import *

name = "Strip"
author = "Ciaran"

fade = RangeAttr("fade", 1.1, 1.01, 2, 0.01)
color = ColorAttr("Color", Color.white())

def draw():

    for pixel in tree.pixels:
        pixel.set_color(color.get())

        for pixel in tree.pixels:
            pixel.fade(n=fade.get())

        yield
