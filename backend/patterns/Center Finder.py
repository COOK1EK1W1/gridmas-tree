from gridmas import *

name = "Center Finder"
author = "Ciaran"


portion = RangeAttr("position", 0, -1, 1, 0.01)
def draw():
    global portion

    for pixel in pixels():
        if pixel.y > portion.get():
            pixel.set_rgb(200, 0, 0)
        else:
            pixel.set_rgb(0, 0, 200)
