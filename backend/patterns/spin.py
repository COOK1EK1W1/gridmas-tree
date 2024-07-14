import math
from colors import Color
from attribute import RangeAttr, ColorAttr

from tree import tree

name = "Spin"
author = "Ciaran"
# based on Matt Parkers xmas tree


def run():
    print("adding colors")
    speed = RangeAttr("speed", 0.1, -0.3, 0.3, 0.01)
    color1 = ColorAttr("color 1", Color(0, 50, 50))
    color2 = ColorAttr("color 2", Color(50, 50, 0))

    heights: list[float] = []
    for i in tree.coords:
        heights.append(i[2])

    angle = 0

    # the starting point on the vertical axis
    c = -tree.height / 2
    while True:

        print(angle)

        for pixel in tree.pixels:
            # figure out if the pixel is above or below the plane
            if (math.tan(angle) * pixel.x <= pixel.z + c) ^ (angle > 0.5 * math.pi) ^ (angle >= 1.5 * math.pi):
                pixel.set_color(color1.get())
            else:
                pixel.set_color(color2.get())

        # use the show() option as rarely as possible as it takes ages
        # do not use show() each time you change a LED but rather wait until you have changed them all
        tree.update()

        # now we get ready for the next cycle

        angle += speed.get() % 2 * math.pi
