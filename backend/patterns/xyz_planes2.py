from colors import Color
import math
from animations.wipe import wipe_frames
from attribute import RangeAttr

name = "XYZ Planes2"
author = "Ciaran"


def run():

    dirs = [(0, 0), (math.pi / 2, 0), (math.pi / 2, math.pi / 2), (math.pi / 2, math.pi), (math.pi / 2, math.pi * 1.5), (math.pi, 0)]

    color = Color.random()
    speed = RangeAttr("speed", 45, 30, 60, 1)
    while True:
        for dir in dirs:
            color = Color.different_from(color)
            wipe_frames(dir[0], dir[1], color, int(speed.get()), Color.black())
