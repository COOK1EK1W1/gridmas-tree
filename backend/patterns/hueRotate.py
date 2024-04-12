from util import tree
import time
import util

name = "HueRotate"
display_name = "Hue Rotate"
author = "Ciaran"

def run():
    hue = 0
    while True:
        hue = (hue + 0.02) % 1
        r, g, b = util.hsl_to_rgb(hue, 1, 0.5)
        for i in range(len(tree.pixels)):
            color = (r, g, b)
            tree.set_light(i, color)
        tree.update()
        time.sleep(1/30)
