import math
import random
from attribute import RangeAttr, ColorAttr
from tree import tree
from colors import Color

name = "Aurora Borealis"
author = "Claude 3.5"


def interpolate_color(color1, color2, factor):
    return Color(
        int(color1.r + (color2.r - color1.r) * factor),
        int(color1.g + (color2.g - color1.g) * factor),
        int(color1.b + (color2.b - color1.b) * factor)
    )


def run():
    flow_speed = RangeAttr("Flow Speed", 0.02, 0.01, 0.1, 0.01)
    color_shift_speed = RangeAttr("Color Shift Speed", 0.01, 0.001, 0.05, 0.001)
    wave_frequency = RangeAttr("Wave Frequency", 1.5, 0.5, 3.0, 0.1)
    sparkle_chance = RangeAttr("Sparkle Chance", 0.0005, 0.0001, 0.01, 0.0001)

    color1 = ColorAttr("Color 1", Color(0, 255, 100))  # Green
    color2 = ColorAttr("Color 2", Color(100, 200, 255))  # Light blue
    color3 = ColorAttr("Color 3", Color(255, 100, 200))  # Pink

    time = 0
    while True:
        for i, pixel in enumerate(tree.pixels):
            # Calculate the base wave using the pixel's x and y coordinates
            wave = math.sin(wave_frequency.get() * (pixel.x + pixel.y) + time)

            # Add vertical movement
            wave += math.sin(wave_frequency.get() * 0.5 * pixel.z + time * 1.5)

            # Normalize the wave to [0, 1]
            wave = (wave + 2) / 4

            # Calculate color based on the wave and time
            if wave < 0.33:
                factor = wave * 3
                color = interpolate_color(color1.get(), color2.get(), factor)
            elif wave < 0.67:
                factor = (wave - 0.33) * 3
                color = interpolate_color(color2.get(), color3.get(), factor)
            else:
                factor = (wave - 0.67) * 3
                color = interpolate_color(color3.get(), color1.get(), factor)

            # Add occasional sparkle
            if random.random() < sparkle_chance.get():
                color = Color(255, 255, 255)  # White sparkle

            tree.set_light(i, color)

        tree.update()
        time += flow_speed.get()

        # Slowly shift the colors over time
        hue_shift = color_shift_speed.get()
        color1.set(Color.fromHSL((time * hue_shift) % 1, 1, 0.5))
        color2.set(Color.fromHSL(((time * hue_shift) + 0.33) % 1, 1, 0.6))
        color3.set(Color.fromHSL(((time * hue_shift) + 0.67) % 1, 1, 0.7))
