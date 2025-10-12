import random
from gridmas import *

star_color = Color(255, 255, 255)  # Star color - white
sky_color = Color(15, 15, 40)  # Dark "sky" color - deep blue
twinkling_frequency = 0.1  # Chance of a light twinkling each second

def draw():
    for pixel in pixels():
        if random.random() < twinkling_frequency:
            if random.random() > 0.5:
                pixel.set_color(star_color)
            else:
                pixel.set_color(sky_color)


