from tree import tree
import random


def fizzle():
    a = list(range(tree.num_pixels))
    random.shuffle(a)
    for i in a:
        tree.pixels[i].set_rgb(0, 0, 0)
        tree.update()
