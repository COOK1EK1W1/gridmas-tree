# Solid Color

By _Ciaran_

```py linenums="1"
from attribute import ColorAttr
from colors import Color
from tree import tree

name = "Solid Color"
author = "Ciaran"


def run():
    col = ColorAttr("Color", Color(200, 20, 0))
    tree.set_fps(45)
    while True:
        for pixel in tree.pixels:
            pixel.set_color(col.get())
        tree.update()

```