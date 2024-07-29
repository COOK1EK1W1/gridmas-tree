from colors import Color
import math
from animations.wipe import wipe

name = "XYZ Planes"
author = "Ciaran"


def run():

    dirs = [(0, 0), (math.pi / 2, 0), (math.pi / 2, math.pi / 2), (math.pi / 2, math.pi), (math.pi / 2, math.pi * 1.5), (math.pi, 0)]

    color = Color.random()
    while True:
        for dir in dirs:
            color = Color.different_from(color)
            wipe(dir[0], dir[1], color, 10, Color.black())
