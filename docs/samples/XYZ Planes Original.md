# XYZ Planes Original
```py linenums="1"
from gridmas import *
import math

name = "XYZ Planes2"
author = "Ciaran"


speed = RangeAttr("speed", 45, 30, 60, 1)
def draw():

    dirs = [(0, 0), (math.pi / 2, 0), (math.pi / 2, math.pi / 2), (math.pi / 2, math.pi), (math.pi / 2, math.pi * 1.5), (math.pi, 0)]

    color = Color.random()
    while True:
        for dir in dirs:
            color = Color.different_from(color)
            yield from wipe_frames(dir[0], dir[1], color, int(speed.get()), Color.black())

```