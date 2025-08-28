from gridmas import *
from colors import Color
import math
from wipe import wipe
from attribute import RangeAttr

name = "XYZ Planes"
author = "Ciaran"


def draw():

    dirs = [(0, 0), (math.pi / 2, math.pi / 2), (math.pi / 2, 0)]

    color = Color.random()
    speed = RangeAttr("speed", 10, 1, 14, 1)
    while True:
        for dir in dirs:
            color = Color.different_from(color)
            yield from wipe(dir[0], dir[1], color, int(speed.get()), Color.black())
