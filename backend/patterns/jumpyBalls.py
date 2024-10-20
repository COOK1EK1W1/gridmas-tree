from particle_system import ParticleSystem, SphereParticle
import random
from colors import Color
from tree import tree


name = "Jumpy Balls"
author = "Ciaran"

class Ball(SphereParticle):
    def __init__(self):

        super().__init__(random.random() - 0.5, random.random()-0.5, tree.height, 0.2, 100, Color.random())
        self.xVel = (random.random() - 0.5) * 0.3
        self.yVel = (random.random() - 0.5) * 0.3
        self.zVel = (1 - random.random()) * 0.03

    def advance(self):
        self.zVel -= 0.03
        self.z += self.zVel
        self.x += self.xVel
        self.y += self.yVel

        if self.z < 0:
            self.zVel *= -0.9
            self.z = 0.1
        if self.x > 0.8 or self.x < -0.8:
            self.xVel *= -0.9
            self.yVel += (random.random() - 0.5) * 0.1
        if self.y > 0.8 or self.y < -0.8:
            self.yVel *= -0.9
            self.xVel += (random.random() - 0.5) * 0.1




def run():

    particle_system = ParticleSystem(tree)


    while True:
        particle_system.add_particle(Ball())
        for _ in range(random.randrange(50, 100)):
            tree.lerp(Color(0, 0, 0), 5)
            particle_system.draw()
            particle_system.advance()
            tree.update()
