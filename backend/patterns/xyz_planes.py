from colors import Color
import math
from animations.wipe import wipe
from attribute import RangeAttr

name = "XYZ Planes"
author = "Ciaran"


def run():

    dirs = [(0, 0), (math.pi / 2, math.pi / 2, (math.pi / 2, 0))]

    color = Color.random()
    speed = RangeAttr("speed", 7, 1, 14, 1)
    while True:
        for dir in dirs:
            color = Color.different_from(color)
            wipe(dir[0], dir[1], color, int(speed.get()), Color.black())
