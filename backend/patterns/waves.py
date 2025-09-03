from gridmas import *
import random


name = "Waves"
author = "Ciaran"

speed = RangeAttr("Speed", 45, 30, 90, 1)
length = RangeAttr("Length", 45, 30, 90, 1)

def draw():
    color = Color.random()
    while True:
        theta = random.uniform(0, 6.28)
        alpha = random.uniform(0, 6.28)
        yield from wipe_wave_frames(theta, alpha, color, int(speed.get()), int(length.get()))
        color = Color.different_from(color)
