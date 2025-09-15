from gridmas import *

def draw():
    color = Color.random()
    while True:
        for pixel in pixels():
            pixel.lerp(color, 50, fn=ease_in_out_expo)

        yield from sleep(100)

        color = Color.different_from(color)
