# Caduceus
```py linenums="1"
from gridmas import *
import random
import math

name = "Caduceus"
author = "Ciaran"

radius = 0.15


class Particle:
    def __init__(self):
        self.z = -radius
        self.angle = random.random() * 2 * math.pi
        self.dist = random.randint(2, 7) / 10
        self.pitch = random.randint(15, 25) / 100
        self.speed = random.randint(3, 10) / 100
        self.col = Color.random()

particles = []

def draw():
    global particles
    particles = list(filter(lambda x: x.z < height(), particles))

    for p in particles:
        p.z += p.speed
        p.angle += p.pitch
        p.x = p.dist * math.sin(p.angle)
        p.y = p.dist * math.cos(p.angle)
        Sphere([p.x, p.y, p.z], radius, p.col)
        
    lerp(Color.black(), 10)

    if frame() % 20 == 0:
        particles.append(Particle())


```