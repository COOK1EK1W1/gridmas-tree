from attribute import RangeAttr

from tree import tree

name = "Center Finder"
author = "Ciaran"
# based on Matt Parkers Xmas tree


def run():
    portion = RangeAttr("plane", 0, -1, 1, 0.01)
    while True:
        for pixel in tree.pixels:
            if pixel.y > portion.get():
                pixel.set_rgb(200, 0, 0)
            else:
                pixel.set_rgb(0, 0, 200)
        tree.update()
