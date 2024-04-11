import time
import random
from util import tree

name = "TwinklingStars"
display_name = "Twinkling Stars"
author = "chatGPT"


def run():
    star_color = (255, 255, 255)  # Star color - white
    sky_color = (15, 15, 40)  # Dark "sky" color - deep blue
    twinkling_frequency = 0.1  # Chance of a light twinkling each second

    # First, color the entire tree in dark sky color
    for i in range(tree.num_pixels):
        tree.set_light(i, sky_color)

    # Update the tree initially
    tree.update()

    while True:
        for i in range(tree.num_pixels):
            # Randomly decide if a light should twinkle
            if random.random() < twinkling_frequency:
                # Randomly choose if this light will twinkle or be turned as sky color
                if random.random() > 0.5:
                    tree.set_light(i, star_color)
                else:
                    tree.set_light(i, sky_color)

        # Update the tree display
        tree.update()

        # Pause for a short time to give a twinkling effect
        time.sleep(1/30)  # Update the frame every 1/30 of a second
