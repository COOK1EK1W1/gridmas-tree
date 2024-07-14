import random
import math
from particle_system import ParticleSystem, SphereParticle
from tree import tree
from colors import Color

name = "Caduceus"
author = "Ciaran"

radius = 0.15


class Snake(SphereParticle):
    def __init__(self):
        super().__init__(0, 0, -radius, radius, 200, Color.random())
        self.angle = random.random() * 2 * math.pi
        self.dist = random.randint(2, 7) / 10
        self.pitch = random.randint(15, 25) / 100
        self.speed = random.randint(3, 10) / 100

    def advance(self):
        self.z += self.speed
        dist = self.dist * ((self.z / - tree.height) + 1)
        self.angle += self.pitch
        self.x = dist * math.sin(self.angle)
        self.y = dist * math.cos(self.angle)

        if (self.z > tree.height + radius):
            self.is_dead = True


def run():
    particle_system = ParticleSystem(tree)

    while True:
        for _ in range(random.randint(5, 20)):

            tree.fade()

            particle_system.drawParticles()
            particle_system.advance()

        particle_system.add_particle(Snake())
