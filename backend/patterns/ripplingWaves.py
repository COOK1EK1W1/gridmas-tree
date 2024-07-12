import math
from attribute import RangeAttr, ColorAttr
from tree import tree
from colors import Color

name = "Rippling Waves"
author = "Claude 3.5"


def run():
    wave_speed = RangeAttr("Wave Speed", 0.1, 0.01, 0.5, 0.01)
    wave_frequency = RangeAttr("Wave Frequency", 2.0, 0.5, 5.0, 0.1)
    color_speed = RangeAttr("Color Speed", 0.02, 0.01, 0.1, 0.01)
    primary_color = ColorAttr("Primary Color", Color(255, 0, 0))
    secondary_color = ColorAttr("Secondary Color", Color(0, 0, 255))

    time = 0
    while True:
        for i, pixel in enumerate(tree.pixels):
            # Calculate the wave based on height (z-coordinate) and time
            wave = math.sin(wave_frequency.get() * (pixel.z / tree.height * 2 * math.pi + time))

            # Map the wave to a value between 0 and 1
            wave_mapped = (wave + 1) / 2

            # Interpolate between primary and secondary colors
            r = int(primary_color.get().r * wave_mapped + secondary_color.get().r * (1 - wave_mapped))
            g = int(primary_color.get().g * wave_mapped + secondary_color.get().g * (1 - wave_mapped))
            b = int(primary_color.get().b * wave_mapped + secondary_color.get().b * (1 - wave_mapped))

            # Add a radial component based on distance from the center
            distance = math.sqrt(pixel.x**2 + pixel.y**2)
            radial_factor = (math.sin(distance * wave_frequency.get() * 2 + time) + 1) / 2

            # Combine the vertical wave with the radial component
            combined_factor = (wave_mapped + radial_factor) / 2

            # Set the final color
            tree.set_light(i, Color(
                int(r * combined_factor),
                int(g * combined_factor),
                int(b * combined_factor)
            ))

        tree.update()
        time += wave_speed.get()

        # Slowly shift the primary and secondary colors
        hue_shift = color_speed.get()
        primary_color.set(Color.fromHSL((time * hue_shift) % 1, 1, 0.5))
        secondary_color.set(Color.fromHSL(((time * hue_shift) + 0.5) % 1, 1, 0.5))
