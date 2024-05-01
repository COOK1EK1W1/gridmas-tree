import random
from util import tree
from colors import Color

name = "TwinklingStars"
display_name = "Twinkling Stars"
author = "chatGPT"


def run():
    star_color = Color(255, 255, 255)  # Star color - white
    sky_color = Color(15, 15, 40)  # Dark "sky" color - deep blue
    twinkling_frequency = 0.1  # Chance of a light twinkling each second

    # First, color the entire tree in dark sky color
    for pixel in tree.pixels:
        pixel.set_color(sky_color)

    # Update the tree initially
    tree.update()

    while True:
        for pixel in tree.pixels:
            if random.random() < twinkling_frequency:
                if random.random() > 0.5:
                    pixel.set_color(star_color)
                else:
                    pixel.set_color(sky_color)

        # Update the tree display
        tree.update()
