import random
from tree import tree

name = "murca"
author = "Ciaran"

def run():
    y = 0

    stars = [random.randint(0, tree.num_pixels) for _ in range(100)]

    while True:
        y = (y + 0.01) % tree.height
        for pixel in tree.pixels:
            if ((pixel.z + y) % tree.height * 2 >= tree.height):
                # do stars
                pixel.set_RGB(0, 0, 255)

        for star in stars:
            tree.pixels[star].set_RGB(200, 200, 200)

        for pixel in tree.pixels:
            if not ((pixel.z + y) % tree.height * 2 >= tree.height):
                if (pixel.x % 0.6) > 0.3:
                    pixel.set_RGB(255, 0, 0)
                else:
                    pixel.set_RGB(200, 200, 200)
        tree.update()
