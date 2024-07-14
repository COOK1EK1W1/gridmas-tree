from tree import tree
import random
from particle_system import ParticleSystem, SphereParticle
from colors import Color


name = "Snowing"
author = "Ciaran"

fallSpeed = 0.1


class SnowFlake(SphereParticle):
    def __init__(self, x, y):
        super().__init__(x, y, tree.height + 1, 0.02, 100, Color(200, 200, 240))
        self.yVel = 0.05

    def advance(self):
        self.z -= self.yVel
        self.yVel += 0.002


def run():
    particle_system = ParticleSystem(tree)

    while True:
        for _ in range(random.randint(5, 30)):

            tree.fade()

            particle_system.drawParticles()
            particle_system.advance()

        particle_system.add_particle(SnowFlake(random.random() - 0.5, random.random() - 0.5))
