from tree import tree
import random
print(random.shuffle(list(range(500))))


def fizzle():
    a = list(range(500))
    random.shuffle(a)
    for i in a:
        tree.pixels[i].set_rgb(0, 0, 0)
        tree.update()

