from util import tree
import time

name = "checkers"
display_name = "Checkers"
author = "Ciaran"


def run():
    for i, pixel in enumerate(tree.pixels):
        x = 0
        if tree.coords[i][0] % 2 > 1:
            x ^= 1
        if tree.coords[i][1] % 2 > 1:
            x ^= 1
        if tree.coords[i][2] % 2 > 1:
            x ^= 1
        if x == 0:
            tree.set_light(i, (0, 0, 0))
        else:
            tree.set_light(i, (0, 0, 255))
    tree.update()
    time.sleep(1)
