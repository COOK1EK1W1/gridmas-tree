from colors import Color
from tree import tree

name = "Lerpy"
author = "Ciaran"


def run():
    color = Color.random()
    tree.set_fps(41)
    while True:
        for pixel in tree.pixels:
            pixel.lerp(color.to_tuple(), 5)

        tree.sleep(20, allow_lerp=True)

        color = Color.different_from(color)
