from gridmas import *
import random



name = "Snowing"
author = "Ciaran"


class SnowFlake:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.z = tree.height + 0.2
        self.yVel = 0.05


def draw():
    flakes = []

    while True:
        for _ in range(random.randint(5, 30)):

            flakes = list(filter(lambda x: x.z > -0.2, flakes))
            tree.fade()

            for flake in flakes:
                Sphere((flake.x, flake.y, flake.z), 0.2, Color(200, 200, 240))
                flake.z -= flake.yVel
                flake.yVel += 0.002

            yield

        flakes.append(SnowFlake(random.random() - 0.5, random.random() - 0.5))
