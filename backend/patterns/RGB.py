from util import tree
import time

def run():
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
        time.sleep(1)
