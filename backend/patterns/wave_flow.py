import time
import math

from attribute import RangeAttr
from tree import tree
from colors import Color

name = "Wave Flow"
author = "chatGPT"


def run():
    WAVE_SPEED = RangeAttr("Wave speed", 0.03, 0.01, 0.05, 0.01)
    WAVE_PERIOD = RangeAttr("Wave period", 0.5, 0.1, 1, 0.1)
    COLOR_CHANGE_RATE = RangeAttr("Color change rate", 0.2, 0.06, 0.8, 0.02)
    wave_offset = 0  # This will move the wave up along the z-axis (height)

    while True:
        # Slowly change color over time for the wave (rainbow-like cycle)
        r = int((math.sin(COLOR_CHANGE_RATE.get() * time.time()) + 1) / 2 * 255)
        g = int((math.sin(COLOR_CHANGE_RATE.get() * time.time() + 2 * math.pi / 3) + 1) / 2 * 255)
        b = int((math.sin(COLOR_CHANGE_RATE.get() * time.time() + 4 * math.pi / 3) + 1) / 2 * 255)
        wave_color = (r, g, b)

        for pixel in tree.pixels:
            # A basic 3D wave function based on the z-coordinate and a changing 'wave_offset'
            intensity = 0.5 * (math.cos(2 * math.pi * (pixel.z / tree.height + wave_offset) / WAVE_PERIOD.get()) + 1)
            # Using intensity to modify the brightness of the color
            wave_intensity_color = Color(int(wave_color[0] * intensity), int(wave_color[1] * intensity), int(wave_color[2] * intensity))

            # Set the light to the calculated color
            pixel.set_color(wave_intensity_color)

        # Update the display to reflect changes
        tree.update()
        # Increase the wave offset to move the wave upwards
        wave_offset = (wave_offset + WAVE_SPEED.get()) % (6)
