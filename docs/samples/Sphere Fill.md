# Sphere Fill
```py linenums="1"
import math
from gridmas import *

name = "Spin"
author = "Ciaran"
# based on Matt Parkers xmas tree

speed = RangeAttr("speed", 0.02, -0.1, 0.1, 0.001)
color1 = ColorAttr("color 1", Color(0, 50, 50))
color2 = ColorAttr("color 2", Color(50, 50, 0))

heights: list[float] = []
for i in coords():
    heights.append(i[2])

angle = 0

# the starting point on the vertical axis
c = -height() / 2

def draw():
    global angle

    for pixel in pixels():
        # figure out if the pixel is above or below the plane
        if (math.tan(angle) * pixel.x <= pixel.z + c) ^ (angle > 0.5 * math.pi) ^ (angle >= 1.5 * math.pi):
            pixel.set_color(color1.get())
        else:
            pixel.set_color(color2.get())

    # now we get ready for the next cycle

    angle = (angle + speed.get()) % (2 * math.pi)

```