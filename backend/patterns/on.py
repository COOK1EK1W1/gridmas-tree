from prelude import *

i = 0
def draw():
    global i
    for pixel in tree.pixels:
        if pixel.z < i:
            pixel.set_rgb(200, 55, 2)

    i += tree.height / 70
