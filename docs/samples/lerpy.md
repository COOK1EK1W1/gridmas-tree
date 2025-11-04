# Lerpy
```py linenums="1"
from gridmas import *

name = "Lerpy"
author = "Ciaran"


def draw():
    color = Color.random()
    while True:
        for pixel in pixels():
            pixel.lerp(color, 50, fn=ease_in_out_expo)

        for _ in range(100):
            yield
            
        color = Color.different_from(color)

```