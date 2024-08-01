from tree import tree
from colors import Color
import math


def run(color: Color):
    for rng in range(0, int(tree.height * 200), 10):
        for pixel in tree.pixels:
            if rng <= pixel.z * 200 < rng + 10:
                pixel.set_color(color)
        tree.update()


def wipe(theta: float, alpha: float, color: Color, speed: int, fade: Color | None = None):
    # based on Matt Parkers Xmas tree
    coords2 = [[x, y, z] for [x, y, z] in tree.coords]
    for i, coord in enumerate(tree.coords):
        coords2[i][2] = math.sin(theta) * (coord[0] * math.sin(alpha) + coord[1] * math.cos(alpha)) + coord[2] * math.cos(theta)

    minZ = min([x[2] for x in coords2])
    maxZ = max([x[2] for x in coords2])

    color = Color.different_from(color)

    for rng in range(int(minZ * 200 - 10), int(maxZ * 200 + 10), speed):
        for i, coord in enumerate(coords2):
            if rng <= coord[2] * 200 < rng + 10:
                tree.set_light(i, color)
            else:
                if fade:
                    tree.get_light(i).lerp(fade.to_tuple(), 50)
        tree.update()
