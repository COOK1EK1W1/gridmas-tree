import random
from attribute import RangeAttr
from colors import Color
from animations.wipe import wipe


name = "Chem planes"
author = "Ciaran"


def run():
    color = Color(255, 255, 0)
    speed = RangeAttr("speed", 10, 1, 20, 1)
    while True:
        theta = random.uniform(0, 6.28)
        alpha = random.uniform(0, 6.28)
        wipe(theta, alpha, color, int(speed.get()), Color.black())
        color = Color.different_from(color)
