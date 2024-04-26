from util import tree
import time
from colors import Color
from attribute import RangeAttr

name = "HueRotate"
display_name = "Hue Rotate"
author = "Ciaran"


def run():
    hue = 0
    speed = RangeAttr("speed", 0.02, 0.01, 0.1, 0.01)
    while True:
        hue = (hue + speed.get()) % 1
        for i in range(len(tree.pixels)):
            tree.set_light(i, Color.fromHSL(hue, 1, 0.5))
        tree.update()
        time.sleep(1 / 30)
