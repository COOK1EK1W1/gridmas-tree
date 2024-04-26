from util import tree
import time
from colors import Color

name = "checkers"
display_name = "Checkers"
author = "Ciaran"


def run():
    while True:
        color1 = Color.random()
        color2 = Color.random()
        for i in range(len(tree.pixels)):
            x = 0
            if tree.coords[i][0] % 2 > 1:
                x ^= 1
            if tree.coords[i][1] % 2 > 1:
                x ^= 1
            if tree.coords[i][2] % 2 > 1:
                x ^= 1
            if x == 0:
                tree.set_light(i, color1)
            else:
                tree.set_light(i, color2)
        tree.update()
        time.sleep(1)
