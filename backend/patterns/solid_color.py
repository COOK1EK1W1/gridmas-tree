from gridmas import *

name = "Solid Color"
author = "Ciaran"

col = ColorAttr("Color", Color(200, 20, 0))

def draw():
    for pixel in tree.pixels:
        pixel.set_color(col.get())
