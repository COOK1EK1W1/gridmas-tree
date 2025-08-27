from prelude import *
import math


def draw():

    dirs = [(0, 0), (math.pi / 2, math.pi / 2), (math.pi / 2, 0)]

    color = Color.random()
    speed = 10
    while True:
        for dir in dirs:
            color = Color.different_from(color)
            yield from wipe(dir[0], dir[1], color, int(speed), Color.black())
