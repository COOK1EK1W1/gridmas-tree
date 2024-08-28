import random
from colors import Color
from util import euclidean_distance
from tree import tree

name = "Fire Works"
author = "Ciaran"


class Explosion:
    def __init__(self, x, y, z, max_age):
        self.x = x
        self.y = y
        self.z = z
        self.max_age = max_age
        self.tick = 0
        self.color = Color.random()


def run():
    explosions: list[Explosion] = []
    i = 0
    interval = 50
    while True:
        if i == 0:
            randomid = random.randrange(0, tree.num_pixels - 1)
            center_light = tree.get_light(randomid)
            explosions.append(Explosion(center_light.x, center_light.y, center_light.z, 5))
            interval = random.randrange(50, 140)
        i = (i + 1) % interval

        for exp in explosions:
            exp.tick += 1

        for pixel in tree.pixels:
            a = random.random()
            if a > 0.8:
                pixel.fade(random.randrange(100, 120, 1) / 100)
            elif a > 0.77:
                pixel.set_color(Color.black())
            elif a > 0.765:
                pixel.fade(0.5)

            for exp in explosions:
                if exp.tick / 6 < euclidean_distance([exp.x, exp.y, exp.z], [pixel.x, pixel.y, pixel.z]) < exp.tick / 5:
                    pixel.set_color(exp.color)

        tree.update()
        explosions = list(filter(lambda x: x.tick <= x.max_age, explosions))
