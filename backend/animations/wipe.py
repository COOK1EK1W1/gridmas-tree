

from tree import tree
from colors import Color

def run(dir, color):
    for rng in range(0, int(tree.height * 200), 10):
        for pixel in tree.pixels:
            if rng <= pixel.z * 200 < rng + 10:
                pixel.set_color(Color(200, 55, 2))
        tree.update()
