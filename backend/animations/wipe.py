

from util import tree
from colors import Color

def run(dir, color):
    for rng in range(0, int(tree.height * 200), 10):
        for i in range(len(tree.pixels)):
            if rng <= tree.coords[i][2] * 200 < rng + 10:
                tree.set_light(i, Color(200, 55, 2))
        tree.update()
