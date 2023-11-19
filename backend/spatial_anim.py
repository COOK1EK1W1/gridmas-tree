import random
import time
import threading
import math

from util import tree


def xyz_planes(stopFlag: threading.Event):
    j = 1.1
    fps = 1/60
    rng = 10

    idk = 0
    while not stopFlag.is_set():
        idk = (idk + 1) % 3
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        for i in range(-200, 200, rng):
            for ia, coord in enumerate(tree.coords):
                if i <= (coord[idk % 3] * 200) < i + rng:
                    tree.set_light(ia, color)
                else:
                    r, g, b = tree.get_light(ia)
                    tree.set_light(ia, (int(r/j), int(g/j), int(b/j)))
            tree.update()
            time.sleep(fps)
            if stopFlag.is_set():
                break
        idk = (idk + 1) % 3
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        for i in range(0, int(tree.height*200), rng):
            for ia, light in enumerate(tree.coords):
                if i <= (light[idk % 3] * 200) < i + rng:
                    tree.set_light(ia, color)
                else:
                    r, g, b = tree.get_light(ia)
                    tree.set_light(ia, (int(r/j), int(g/j), int(b/j)))
            tree.update()
            time.sleep(fps)
            if stopFlag.is_set():
                break
        idk = (idk + 1) % 3
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        for i in range(-200, 200, rng):
            for ia, coord in enumerate(tree.coords):
                if i <= (coord[idk % 3] * 200) < i + rng:
                    tree.set_light(ia, color)
                else:
                    r, g, b = tree.get_light(ia)
                    tree.set_light(ia, (int(r/j), int(g/j), int(b/j)))
            tree.update()
            time.sleep(fps)
            if stopFlag.is_set():
                break
        idk = (idk + 1) % 3
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))


def doSpin(stopFlag: threading.Event):
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
    c = -1
    while not stopFlag.is_set():
        time.sleep(0.05)

        for led in range(tree.num_pixels):
            if math.tan(angle)*tree.coords[led][1] <= tree.coords[led][2]+c:
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
