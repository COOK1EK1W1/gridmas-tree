# on
```py linenums="1"
from gridmas import *

i = 0
def draw():
    global i
    for pixel in pixels():
        if pixel.z < i:
            pixel.set_rgb(200, 55, 2)

    i += height() / 70

```