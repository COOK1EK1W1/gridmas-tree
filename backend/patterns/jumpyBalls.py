from particle_system import ParticleSystem, SphereParticle
import random
from colors import Color
from tree import tree


name = "Jumpy Balls"
author = "Ciaran"

class Ball(SphereParticle):
    def __init__(self):

        super().__init__(random.random() - 0.5, random.random()-0.5, tree.height, 0.2, 100, Color.random())
        self.xVel = (random.random() - 0.5) * 0.4
        self.yVel = (random.random() - 0.5) * 0.4
        self.zVel = (1 - random.random()) * 0.03

    def advance(self):
        self.zVel -= 0.06
        self.z += self.zVel
        self.x += self.xVel
        self.y += self.yVel

        if self.z < 0:
            self.zVel *= -0.9
            self.z = 0.1
        if self.x > 1 or self.x < -1:
            self.xVel *= -0.9
        if self.y > 1 or self.y < -1:
            self.yVel *= -0.9




def run():

    particle_system = ParticleSystem(tree)

    particle_system.add_particle(Ball())

    while True:
        particle_system.add_particle(Ball())
        for _ in range(20):
            tree.black()
            particle_system.draw()
            particle_system.advance()
            tree.update()
