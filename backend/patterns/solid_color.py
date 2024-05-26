import time

from attribute import ColorAttr
from colors import Color
from util import tree

name = "Solid Color"
author = "Ciaran"


def run():
    col = ColorAttr("Color", Color(200, 20, 0))
    while True:
        for pixel in tree.pixels:
            pixel.set_color(col.get())
        tree.update()
        time.sleep(1)
