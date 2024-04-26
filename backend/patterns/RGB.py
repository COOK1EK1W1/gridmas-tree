from attribute import RangeAttr
from util import tree
import time

name = "RGB"
display_name = "RGB"
author = "Ciaran"


def run():
    sleep_time = RangeAttr("sleep time", 1, 0.1, 3, 0.1)

    offset = 0
    while True:
        offset = (offset + 1) % 3

        for i in range(len(tree.pixels)):
            r = 255 if (i+offset) % 3 == 0 else 0
            g = 255 if (i+offset) % 3 == 1 else 0
            b = 255 if (i+offset) % 3 == 2 else 0
            color = (r, g, b)
            tree.set_light(i, color)
        tree.update()
        print(sleep_time.get())
        time.sleep(sleep_time.get())
