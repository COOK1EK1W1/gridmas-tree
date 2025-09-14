import random
import math

from gridmas import *

name = "Wandering Ball"
author = "Ciaran"


height = 0.5
angle = random.randrange(0, 627) / 100
angle2 = random.randrange(0, 627) / 100

dist = 0.3
radius = RangeAttr("radius", 0.4, 0.1, 0.8, 0.03)
color = ColorAttr("ball color", Color.white())
trailLength = RangeAttr("Trail Length", 100, 5, 200, 5)

def draw():
    global angle, height, angle2, dist
    tree.lerp(Color.black(), int(trailLength.get()))

    angle = (angle + 0.1) % 6.28
    angle2 = (angle2 + 0.034) % 6.28

    center = [dist * math.sin(angle), dist * math.cos(angle), height]
    height = abs(math.sin(angle2)) * (tree.height - radius.get() * 2) + radius.get()
    Sphere((center[0], center[1], height), radius.get(), color.get())

