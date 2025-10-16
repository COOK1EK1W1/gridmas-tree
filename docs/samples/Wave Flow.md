# Wave Flow
```py linenums="1"
from gridmas import *
import time
import math

wave_offset = 0  # this will move the wave up along the z-axis (height)
def draw():
    global wave_offset
    wave_speed = 0.03
    wave_period = 0.5
    color_change_rate = 0.2

    # slowly change color over time for the wave (rainbow-like cycle)
    r = int((math.sin(color_change_rate * time.time()) + 1) / 2 * 255)
    g = int((math.sin(color_change_rate * time.time() + 2 * math.pi / 3) + 1) / 2 * 255)
    b = int((math.sin(color_change_rate * time.time() + 4 * math.pi / 3) + 1) / 2 * 255)
    wave_color = (r, g, b)

    for pixel in pixels():
        # a basic 3d wave function based on the z-coordinate and a changing 'wave_offset'
        intensity = 0.5 * (math.cos(2 * math.pi * (pixel.z / height() + wave_offset) / wave_period) + 1)
        # using intensity to modify the brightness of the color
        wave_intensity_color = Color(int(wave_color[0] * intensity), int(wave_color[1] * intensity), int(wave_color[2] * intensity))

        # set the light to the calculated color
        pixel.set_color(wave_intensity_color)

        # increase the wave offset to move the wave upwards
    wave_offset = (wave_offset + wave_speed) % (6)

```