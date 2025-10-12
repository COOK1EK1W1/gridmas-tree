# Twinkle

By _Ciaran_

```py linenums="1"
from tree import tree
import random
from colors import Color
from attribute import ColorAttr

name = "Twinkle"
author = "Ciaran"


def run():
    baseColor = ColorAttr("color", Color(120, 20, 0))
    while True:
        tr, tg, tb = baseColor.get().to_tuple()
        x = random.randint(0, tree.num_pixels - 1)

        tree.set_light(x, Color.black())

        for pixel in tree.pixels:
            r, g, b = pixel.to_tuple()
            pixel.set_rgb(min(int(r + 5), tr), min(int(g + 5), tg), min(int(b + 5), tb))

        tree.update()

```