from gridmas import *

name = "Checkers"
author = "Ciaran"


def draw():
    if frame() % 100 == 0:
        color1 = Color.random()
        color2 = Color.different_from(color1)
        for pixel in tree.pixels:
            x = 0
            if pixel.x % 2 > 1:
                x ^= 1
            if pixel.y % 2 > 1:
                x ^= 1
            if pixel.z % 2 > 1:
                x ^= 1
            if x == 0:
                pixel.set_color(color1)
            else:
                pixel.set_color(color2)
