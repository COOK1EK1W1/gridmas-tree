from util import tree
import time
import random
from colors import Color
from attribute import ColorAttr

name = "twinkle"
display_name = "Twinkle"
author = "Ciaran"


def run():
    baseColor = ColorAttr("color", Color(120, 20, 0))
    while True:
        x = random.randint(0, tree.num_pixels - 1)
        tree.set_light(x, baseColor.get())
        for ia in range(tree.num_pixels):
            r, g, b = tree.get_light(ia)
            color = Color(min(int(r + 5), 200), min(int(g + 5), 55), min(1, int(b + 5)))
            tree.set_light(ia, color)
        tree.update()
        time.sleep(0.02)
