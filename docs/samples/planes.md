# Planes

By _Ciaran_

```py linenums="1"
import random
from attribute import RangeAttr
from colors import Color
from animations.wipe import wipe_frames


name = "Planes"
author = "Ciaran"
# based on Matt Parkers Xmas tree


def run():
    color = Color(255, 255, 0)
    speed = RangeAttr("speed", 45, 30, 45, 1)
    while True:
        theta = random.uniform(0, 6.28)
        alpha = random.uniform(0, 6.28)
        wipe_frames(theta, alpha, color, int(speed.get()))
        color = Color.different_from(color)

```