# Waves

By _Ciaran_

```py linenums="1"
import random
from animations.wipe import wipe_wave_frames
from attribute import RangeAttr
from colors import Color


name = "Waves"
author = "Ciaran"


def run():
    speed = RangeAttr("Speed", 45, 30, 90, 1)
    length = RangeAttr("Length", 45, 30, 90, 1)
    color = Color.random()
    while True:
        theta = random.uniform(0, 6.28)
        alpha = random.uniform(0, 6.28)
        wipe_wave_frames(theta, alpha, color, int(speed.get()), int(length.get()))
        color = Color.different_from(color)

```