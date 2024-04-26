from util import tree
import time
from colors import Color

name = "HueRotate"
display_name = "Hue Rotate"
author = "Ciaran"


def run():
    hue = 0
    while True:
        hue = (hue + 0.02) % 1
        for i in range(len(tree.pixels)):
            tree.set_light(i, Color.fromHSL(hue, 1, 0.5))
        tree.update()
        time.sleep(1 / 30)
