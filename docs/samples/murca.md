# Murca

Red, White, and *of course* Blue

By _Ciaran_

```py linenums="1"
import random
from tree import tree

name = "murca"
author = "Ciaran"


def run():
    y = 0

    stars = [random.randint(0, tree.num_pixels) for _ in range(100)]

    while True:
        y = (y + 0.01) % tree.height
        for pixel in tree.pixels:
            if ((pixel.z + y) % tree.height * 2 >= tree.height):
                # do stars
                pixel.set_rgb(0, 0, 255)

        for star in stars:
            tree.pixels[star].set_rgb(200, 200, 200)

        for pixel in tree.pixels:
            if not ((pixel.z + y) % tree.height * 2 >= tree.height):
                if (pixel.x % 0.6) > 0.3:
                    pixel.set_rgb(255, 0, 0)
                else:
                    pixel.set_rgb(200, 200, 200)
        tree.update()

```