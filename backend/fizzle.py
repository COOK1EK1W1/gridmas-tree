from tree import tree
import random


def fizzle():
    """fizzle Fizzle out

    Randomly select a light on the tree and turn it off each time the function is called
    """
    a = list(range(num_pixels()))
    random.shuffle(a)
    for i in a:
        pixels()[i].set_rgb(0, 0, 0)
        yield
