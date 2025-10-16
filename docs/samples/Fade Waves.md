# Fade Waves
```py linenums="1"
from gridmas import *
import random


name = "Fade Planes"
author = "Ciaran"

speed = RangeAttr("speed", 45, 30, 90, 1)

def draw():
    color = Color(255, 255, 0)
    while True:
        theta = random.uniform(0, 6.28)
        alpha = random.uniform(0, 6.28)
        yield from wipe_frames(theta, alpha, color, int(speed.get()), Color.black())
        color = Color.different_from(color)

```