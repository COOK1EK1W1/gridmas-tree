import random
import cv2
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
    c = -tree.height/2
    while not stopFlag.is_set():
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


def doPlanes(stopFlag: threading.Event):
    while not stopFlag.is_set():
        color = (random.randint(0, 200), random.randint(
            0, 200), random.randint(0, 200))
        coords2 = [[x, y, z] for [x, y, z] in tree.coords]
        theta = random.uniform(0, 6.28)
        alpha = random.uniform(0, 6.28)
        for i, coord in enumerate(tree.coords):
            coords2[i][2] = math.sin(theta) * (coord[0] * math.sin(alpha) +
                                               coord[1] * math.cos(alpha)) + coord[2] * math.cos(theta)

        minZ = min([x[2] for x in coords2])
        maxZ = max([x[2] for x in coords2])

        for rng in range(int(minZ*200), int(maxZ*200), 10):
            for i, coord in enumerate(coords2):
                if rng <= coord[2]*200 < rng+10:
                    tree.set_light(i, color)
            if stopFlag.is_set():
                break
            tree.update()


def doSphereFill(stopFlag: threading.Event):
    while not stopFlag.is_set():
        color = (random.randint(0, 200), random.randint(
            0, 200), random.randint(0, 200))
        center = [0, 0, tree.height/2]  # Center of the tree

        # Radius expansion parameters
        min_radius = 0.1
        # pythagoras, distance from the centre to the edge
        max_radius = ((tree.height/2) ** 2 + 1) ** 0.5
        expansion_speed = 0.05

        radius = min_radius

        while radius <= max_radius:
            for i, coord in enumerate(tree.coords):
                distance_to_center = math.sqrt(
                    (coord[0] - center[0]) ** 2 +
                    (coord[1] - center[1]) ** 2 +
                    (coord[2] - center[2]) ** 2
                )

                # Check if the current LED is within the expanding sphere
                if distance_to_center <= radius:
                    tree.set_light(i, color)

            # Update the tree display
            tree.update()

            # Pause for a short time to control the expansion speed
            time.sleep(1/45)
            # Increase the radius for the next iteration
            radius += expansion_speed

            if stopFlag.is_set():
                break

        # Clear the tree after the sphere has expanded completely
        tree.update()


def doWanderingBall(stopFlag: threading.Event):
    height = 0.5
    angle = 0

    dist = 0.2
    radius = 0.4
    while not stopFlag.is_set():
        color = (255, 255, 255)

        center = [dist * math.sin(angle), dist * math.cos(angle), height]
        for i, coord in enumerate(tree.coords):
            distance_to_center: float = math.sqrt((coord[0] - center[0]) ** 2 + (
                coord[1] - center[1]) ** 2 + (coord[2] - center[2]) ** 2)

            # Check if the current LED is within the expanding sphere
            if distance_to_center <= radius:
                tree.set_light(i, color)
            else:
                tree.set_light(i, (0, 0, 0))

        time.sleep(1/45)

        angle = (angle + 0.1) % 6.28

        # Clear the tree after the sphere has expanded completely
        tree.update()

def doShowImage():
    img = cv2.imread('stocking.jpg', cv2.IMREAD_COLOR)
    print(img)
    print(img.shape)
    for i in range(tree.num_pixels):
        (x, y, z) = tree.coords[i]
        z = int((z) * ((img.shape[0])/(tree.height + 0.1)))
        x = int((x+1) * (img.shape[1] / 2))
        (b, g, r) = img[z, x]
        print((r, g, b))
        tree.set_light(i, (r, g, b))

    tree.update()
doShowImage()
