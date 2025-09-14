from gridmas import *

name = "Sphere Fill"
author = "Ciaran"

class SphereO:
    def __init__(self):
        self.c = Color.random()
        self.x = 0
        self.y = 0
        self.z = tree.height/2
        self.radius = 0
spheres = []

def draw():
    global spheres
    spheres.append(SphereO())
    spheres = list(filter(lambda x: x.radius < 4, spheres))

    for _ in range(100):
        for sphere in spheres:
            Sphere((sphere.x, sphere.y, sphere.z), sphere.radius, sphere.c)
            
            sphere.radius += 0.01
        yield
