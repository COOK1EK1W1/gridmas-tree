import random
from colors import Color
from util import pythagorasDistance
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
            random_z_coord = (random.randrange(0, int(tree.height * 100), 1)) / 100

            random_x_coord = (random.randrange(-100, 100, 1)) / (100 * (random_z_coord + 1))
            random_y_coord = (random.randrange(-100, 100, 1)) / (100 * (random_z_coord + 1))
            explosions.append(Explosion(random_x_coord, random_y_coord, random_z_coord, 40))
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
                if exp.tick / 2 < pythagorasDistance([exp.x, exp.y, exp.z], [pixel.x, pixel.y, pixel.z]) * 100 < exp.tick / 1.3:
                    pixel.set_color(exp.color)

        tree.update()
        explosions = list(filter(lambda x: x.tick <= x.max_age, explosions))
