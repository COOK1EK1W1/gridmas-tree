import random
import math
from colors import Color

from util import tree

name = "Planes"
author = "Ciaran"
# based on Matt Parkers Xmas tree


def run():
    while True:
        coords2 = [[x, y, z] for [x, y, z] in tree.coords]
        theta = random.uniform(0, 6.28)
        alpha = random.uniform(0, 6.28)
        for i, coord in enumerate(tree.coords):
            coords2[i][2] = math.sin(theta) * (coord[0] * math.sin(alpha) + coord[1] * math.cos(alpha)) + coord[2] * math.cos(theta)

        minZ = min([x[2] for x in coords2])
        maxZ = max([x[2] for x in coords2])

        color = Color.random()

        for rng in range(int(minZ * 200), int(maxZ * 200), 10):
            for i, coord in enumerate(coords2):
                if rng <= coord[2] * 200 < rng + 10:
                    tree.set_light(i, color)
            tree.update()
