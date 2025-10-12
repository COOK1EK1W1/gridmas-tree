from gridmas import *
import math

name = "XYZ Planes"
author = "Ciaran"


speed = RangeAttr("speed", 10, 1, 14, 1)
def draw():

    dirs = [(0, 0), (math.pi / 2, math.pi / 2), (math.pi / 2, 0)]

    color = Color.random()
    while True:
        for dir in dirs:
            color = Color.different_from(color)
            yield from wipe(dir[0], dir[1], color, int(speed.get()), Color.black())
