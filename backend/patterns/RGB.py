from gridmas import *

name = "RGB"
author = "Ciaran"

sleep_time = RangeAttr("sleep time", 45, 20, 40, 1)
offset = 0

def draw():
    global sleep_time, offset

    
    if frame() % sleep_time.get() == 0:
        offset = (offset + 1) % 3

    for i, pixel in enumerate(pixels()):
        r = 255 if (i + offset) % 3 == 0 else 0
        g = 255 if (i + offset) % 3 == 1 else 0
        b = 255 if (i + offset) % 3 == 2 else 0
        pixel.set_rgb(r, g, b)
