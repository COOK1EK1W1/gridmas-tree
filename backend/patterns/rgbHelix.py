import math

import util
from util import tree
import random

name = "rgb_helix"
display_name = "RGB Helix"
author = "Ciaran"


def run():
    twist_dx = 0.01
    twist_amount = -random.randrange(-8, 8)
    speed = 2
    offset = random.random() * math.pi * 2
    color_offset = random.random()
    while True:
        for i, coord in enumerate(tree.coords):
            angle = math.atan2(coord[1], coord[0])

            modified_angle = (angle + coord[2] * twist_amount + offset*speed) % (math.pi * 2)

            a = round((modified_angle) / math.pi)

            hue = a/2
            r, g, b = util.hsl_to_rgb((hue + color_offset) % 1, 1, 0.5)
            tree.set_light(i, (r, g, b))

        tree.update()

        offset = (offset + 0.01) % (math.pi * 2)

        color_offset = (0.00027 + color_offset) % 1

        twist_amount += twist_dx
        if twist_amount > 10:
            twist_dx = -0.01
        elif twist_amount < -10:
            twist_dx = 0.01
        # print(twist_dx, twist_amount, speed, offset, color_offset)
