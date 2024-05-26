import random
import math

from util import tree
from colors import Color
from attribute import ColorAttr, RangeAttr

name = "Wandering Ball"
author = "Ciaran"


def run():
    height = 0.5
    angle = random.randrange(0, 627) / 100
    angle2 = random.randrange(0, 627) / 100

    dist = 0.3
    radius = RangeAttr("radius", 0.4, 0.1, 0.8, 0.1)
    color = ColorAttr("ball color", Color.white())
    trailLength = RangeAttr("Trail Length", 10, 5, 30, 5)
    while True:

        center = [dist * math.sin(angle), dist * math.cos(angle), height]
        height = math.sin(angle2) + tree.height / 2
        for pixel in tree.pixels:
            distance_to_center: float = math.sqrt((pixel.x - center[0]) ** 2 + (pixel.y - center[1]) ** 2 + (pixel.z - center[2]) ** 2)

            # Check if the current LED is within the expanding sphere
            if distance_to_center <= radius.get():
                pixel.set_color(color.get())
            else:
                r, g, b = pixel.toTuple()
                pixel.set_color(Color(max(0, r - trailLength.get()), max(0, g - trailLength.get()), max(0, b - trailLength.get())))

        angle = (angle + 0.1) % 6.28
        angle2 = (angle2 + 0.034) % 6.28

        tree.update()
