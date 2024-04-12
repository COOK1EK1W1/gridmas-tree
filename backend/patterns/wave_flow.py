import time
import math

from util import tree

name = "WaveFlow"
display_name = "Wave Flow"
author = "chatGPT"

# Constants that will help define the pattern's characteristics
WAVE_SPEED = 0.03  # How fast the wave moves up
WAVE_PERIOD = 0.5  # The period of the cosine function, controls the wave density
COLOR_CHANGE_RATE = 0.2  # How quickly the colors cycle through


def run():
    wave_offset = 0  # This will move the wave up along the z-axis (height)

    while True:
        # Slowly change color over time for the wave (rainbow-like cycle)
        r = int((math.sin(COLOR_CHANGE_RATE * time.time()) + 1) / 2 * 255)
        g = int((math.sin(COLOR_CHANGE_RATE * time.time() + 2 * math.pi / 3) + 1) / 2 * 255)
        b = int((math.sin(COLOR_CHANGE_RATE * time.time() + 4 * math.pi / 3) + 1) / 2 * 255)
        wave_color = (r, g, b)

        for i, coord in enumerate(tree.coords):
            # Calculate the wave pattern based on x, y, z
            x, y, z = coord
            # A basic 3D wave function based on the z-coordinate and a changing 'wave_offset'
            intensity = 0.5 * (math.cos(2 * math.pi * (z / tree.height + wave_offset) / WAVE_PERIOD) + 1)
            # Using intensity to modify the brightness of the color
            wave_intensity_color = (int(wave_color[0] * intensity), int(wave_color[1] * intensity), int(wave_color[2] * intensity))

            # Set the light to the calculated color
            tree.set_light(i, wave_intensity_color)

        # Update the display to reflect changes
        tree.update()
        # Increase the wave offset to move the wave upwards
        wave_offset = (wave_offset + WAVE_SPEED) % (2 * math.pi)

        # Pause briefly to control the speed of the effect and reduce CPU usage
        time.sleep(1/30)  # Let's aim for about 30 frames per second
