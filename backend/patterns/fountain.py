from gridmas import *
import math
import random



name = "Fountain"
author = "Ciaran"


class Dropplet:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.zAcl = -0.003
        self.zVel = 0.1
        self.xVel = 0.008
        self.dist = 0
        self.angle = random.random() * 2 * math.pi


def draw():
    snowflakes = []
    while True:
        snowflakes = list(filter(lambda x: x.z > -0.2, snowflakes))

        tree.fade(10)
        for _ in range(random.randint(2, 3)):

            for flake in snowflakes:
                Sphere((flake.x, flake.y, flake.z), 0.15, Color(100,100,240))

                flake.z += flake.zVel
                flake.zVel += flake.zAcl

                flake.x = flake.dist * math.sin(flake.angle)
                flake.y = flake.dist * math.cos(flake.angle)

                flake.dist += flake.xVel

            yield
            
        snowflakes.append(Dropplet())
