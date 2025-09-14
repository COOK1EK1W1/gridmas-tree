# Center Finder

A demonstration of finding the center of the tree by _Ciaran_

```py linenums="1"
from attribute import RangeAttr

from tree import tree

name = "Center Finder"
author = "Ciaran"


def run():
    portion = RangeAttr("position", 0, -1, 1, 0.01)
    while True:
        for pixel in tree.pixels:
            if pixel.y > portion.get():
                pixel.set_rgb(200, 0, 0)
            else:
                pixel.set_rgb(0, 0, 200)
        tree.update()

```