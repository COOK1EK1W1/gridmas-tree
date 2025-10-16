# Twinkle
```py linenums="1"
from gridmas import *
import random

baseColor = ColorAttr("color", Color(120, 20, 0))

def draw():
    tr, tg, tb = baseColor.get().to_tuple()
    x = random.randint(0, num_pixels() - 1)

    set_pixel(x, Color.black())

    for pixel in pixels():
        r, g, b = pixel.to_tuple()
        pixel.set_rgb(min(int(r + 5), tr), min(int(g + 5), tg), min(int(b + 5), tb))


```