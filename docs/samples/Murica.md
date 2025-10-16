# Murica
```py linenums="1"
import random
from gridmas import *

name = "murca"
author = "Ciaran"


def draw():
    y = 0

    stars = [random.randint(0, num_pixels()) for _ in range(100)]

    while True:
        y = (y + 0.01) % height()
        for pixel in pixels():
            if ((pixel.z + y) % height() * 2 >= height()):
                # do stars
                pixel.set_rgb(0, 0, 255)

        for star in stars:
            pixels()[star].set_rgb(200, 200, 200)

        for pixel in pixels():
            if not ((pixel.z + y) % height() * 2 >= height()):
                if (pixel.x % 0.6) > 0.3:
                    pixel.set_rgb(255, 0, 0)
                else:
                    pixel.set_rgb(200, 200, 200)
        yield

```