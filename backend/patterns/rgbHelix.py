import math
import time
from attribute import RangeAttr

from util import tree
from colors import Color
import random

name = "rgb_helix"
display_name = "RGB Helix"
author = "Ciaran"


def run():
    twist_dx = RangeAttr("twist speed", 0.01, 0.001, 0.2, 0.001)
    rotate_amount = RangeAttr("Rotate speed", 0.01, 0.001, 0.05, 0.001)
    twist_dir = 1
    twist_amount = -random.randrange(-8, 8)
    speed = 2
    offset = random.random() * math.pi * 2
    color_offset = random.random()
    while True:
        for i, coord in enumerate(tree.coords):
            angle = math.atan2(coord[1], coord[0])

            modified_angle = (angle + coord[2] * twist_amount + offset * speed) % (math.pi * 2)

            a = round((modified_angle) / math.pi)

            hue = a / 2
            tree.set_light(i, Color.fromHSL((hue + color_offset) % 1, 1, 0.5))

        tree.update()
        time.sleep(1 / 45)

        offset = (offset + rotate_amount.get()) % (math.pi * 2)

        color_offset = (0.00027 + color_offset) % 1

        twist_amount += twist_dir * twist_dx.get()
        if twist_amount > 10:
            twist_dir = -1
        elif twist_amount < -10:
            twist_dir = 1
        # print(twist_dx, twist_amount, speed, offset, color_offset)
