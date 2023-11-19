from util import tree
import random
import time
import threading


def doStrip(stopFlag: threading.Event):
    while not stopFlag.is_set():
        for i in range(tree.num_pixels):
            tree.set_light(i, (255, 255, 255))
            for ia in range(tree.num_pixels):
                r, g, b = tree.get_light(ia)
                tree.set_light(ia, (int(r/1.1), int(g/1.1), int(b/1.1)))
            tree.update()
            time.sleep(0.01)
            if (stopFlag.is_set()):
                break


def doTwinkle(stopFlag: threading.Event):
    while not stopFlag.is_set():
        x = random.randint(0, tree.num_pixels - 1)
        tree.set_light(x, (0, 100, 0))
        for ia in range(tree.num_pixels):
            r, g, b = tree.get_light(ia)
            color = (min(int(r+5), 100), min(int(g+5), 255), min(20, int(b+5)))
            tree.set_light(ia, color)
        tree.update()
        time.sleep(0.02)
