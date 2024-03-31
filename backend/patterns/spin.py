import time
import math

from util import tree

def doSpin():
    heights: list[float] = []
    for i in tree.coords:
        heights.append(i[2])

    angle = 0

    # how much the angle changes per cycle
    inc = 0.1

    # the two colours in GRB order
    # if you are turning a lot of them on at once, keep their brightness down please
    colourA = (0, 50, 50)
    colourB = (50, 50, 0)  # yellow

    # INITIALISE SOME VALUES

    swap01 = 0
    swap02 = 0

    # the starting point on the vertical axis
    c = -tree.height/2
    while True:
        time.sleep(0.05)

        for led in range(tree.num_pixels):
            if math.tan(angle)*tree.coords[led][0] <= tree.coords[led][2]+c:
                tree.set_light(led, colourA)
            else:
                tree.set_light(led, colourB)

        # use the show() option as rarely as possible as it takes ages
        # do not use show() each time you change a LED but rather wait until you have changed them all
        tree.update()

        # now we get ready for the next cycle

        angle += inc
        if angle > 2*math.pi:
            angle -= 2*math.pi
            swap01 = 0
            swap02 = 0

        # this is all to keep track of which colour is 'on top'

        if angle >= 0.5*math.pi:
            if swap01 == 0:
                colourA, colourB = colourB, colourA
                swap01 = 1

        if angle >= 1.5*math.pi:
            if swap02 == 0:
                colourA, colourB = colourB, colourA
                swap02 = 1


