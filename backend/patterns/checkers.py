from util import tree
import time
from colors import Color

name = "Checkers"
author = "Ciaran"


def run():
    while True:
        color1 = Color.random()
        color2 = Color.random()
        for i, pixel in enumerate(tree.pixels):
            x = 0
            if tree.coords[i][0] % 2 > 1:
                x ^= 1
            if tree.coords[i][1] % 2 > 1:
                x ^= 1
            if tree.coords[i][2] % 2 > 1:
                x ^= 1
            if x == 0:
                pixel.set_color(color1)
            else:
                pixel.set_color(color2)
        tree.update()
        time.sleep(1)
