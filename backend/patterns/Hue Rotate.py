from gridmas import *

name = "Hue Rotate"
author = "Ciaran"

hue = 0
speed = RangeAttr("speed", 0.003, -0.005, 0.005, 0.0001)

def draw():
    global hue, speed

    hue = (hue + speed.get()) % 1
    for pixel in pixels():
        pixel.set_hsl(hue, 1, 0.5)

