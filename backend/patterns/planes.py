import random
import math
from attribute import RangeAttr
from colors import Color

from tree import tree

name = "Planes"
author = "Ciaran"
# based on Matt Parkers Xmas tree


def run():
    color = Color(255, 255, 0)
    speed = RangeAttr("speed", 10, 1, 20, 1)
    while True:
        coords2 = [[x, y, z] for [x, y, z] in tree.coords]
        theta = random.uniform(0, 6.28)
        alpha = random.uniform(0, 6.28)
        for i, coord in enumerate(tree.coords):
            coords2[i][2] = math.sin(theta) * (coord[0] * math.sin(alpha) + coord[1] * math.cos(alpha)) + coord[2] * math.cos(theta)

        minZ = min([x[2] for x in coords2])
        maxZ = max([x[2] for x in coords2])

        color = Color.different_from(color)

        for rng in range(int(minZ * 200 - 10), int(maxZ * 200 + 10), max(1, int(speed.get()))):
            for i, coord in enumerate(coords2):
                if rng <= coord[2] * 200 < rng + 10:
                    tree.set_light(i, color)
            tree.update()
