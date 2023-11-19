import random
import time
import threading
import math

import util


def xyz_planes(stopFlag: threading.Event):
    lol = util.read_csv()
    j = 1.1
    fps = 1/60
    rng = 10

    idk = 0
    while not stopFlag.is_set():
        idk = (idk + 1) % 3
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        for i in range(min(lol, key=lambda x: x[idk % 3])[idk % 3], max(lol, key=lambda x: x[idk % 3])[idk % 3], rng):
            for ia, light in enumerate(lol):
                if i <= light[idk % 3] < i + rng:
                    util.setLight(ia, color)
                else:
                    r, g, b = util.get_light(ia)
                    util.setLight(ia, (int(r/j), int(g/j), int(b/j)))
            util.update()
            time.sleep(fps)
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))


def doSpin(stopFlag: threading.Event):
    coords = util.read_csv()
    heights: list[int] = []
    for i in coords:
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
    c = 100
    while not stopFlag.is_set():
        time.sleep(0.05)

        for led in range(len(coords)):
            if math.tan(angle)*coords[led][1] <= coords[led][2]+c:
                util.setLight(led, colourA)
            else:
                util.setLight(led, colourB)

        # use the show() option as rarely as possible as it takes ages
        # do not use show() each time you change a LED but rather wait until you have changed them all
        util.update()

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
