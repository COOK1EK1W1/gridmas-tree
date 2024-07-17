from tree import tree
import math
import random
from particle_system import ParticleSystem, SphereParticle
from colors import Color


name = "Fountain"
author = "Ciaran"


class Dropplet(SphereParticle):
    def __init__(self):
        super().__init__(0, 0, 0, 0.15, 100, Color(100, 100, 240))
        self.zAcl = -0.003
        self.zVel = 0.1
        self.xVel = 0.008
        self.dist = 0
        self.angle = random.random() * 2 * math.pi

    def advance(self):
        self.z += self.zVel
        self.zVel += self.zAcl

        self.x = self.dist * math.sin(self.angle)
        self.y = self.dist * math.cos(self.angle)

        self.dist += self.xVel

        if (self.z < -0.2):
            self.is_dead = True


def run():
    particle_system = ParticleSystem(tree)
    while True:

        for _ in range(random.randint(2, 3)):

            tree.fade()

            particle_system.drawParticles()
            particle_system.advance()
        particle_system.add_particle(Dropplet())
