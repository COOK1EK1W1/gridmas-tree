# Lerpy

By _Ciaran_

```py linenums="1"
from util import ease_in_out_expo
from colors import Color
from tree import tree

name = "Lerpy"
author = "Ciaran"


def run():
    color = Color.random()
    while True:
        for pixel in tree.pixels:
            pixel.lerp(color.to_tuple(), 50, fn=ease_in_out_expo)

        tree.sleep(100, allow_lerp=True)

        color = Color.different_from(color)

```