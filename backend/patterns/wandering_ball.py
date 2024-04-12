import time
import random
import math

from util import tree

name = "wandering_ball"
display_name = "Wandering Ball"
author = "Ciaran"


def run():
    height = 0.5
    angle = random.randrange(0, 627) / 100
    angle2 = random.randrange(0, 627) / 100

    dist = 0.3
    radius = 0.4
    while True:
        color = (255, 255, 255)

        center = [dist * math.sin(angle), dist * math.cos(angle), height]
        height = math.sin(angle2) + tree.height/2
        for i, coord in enumerate(tree.coords):
            distance_to_center: float = math.sqrt((coord[0] - center[0]) ** 2 + (
                coord[1] - center[1]) ** 2 + (coord[2] - center[2]) ** 2)

            # Check if the current LED is within the expanding sphere
            if distance_to_center <= radius:
                tree.set_light(i, color)
            else:
                tree.set_light(i, (max(0, tree.get_light(i)[0]-7), max(0, tree.get_light(i)[1]-10), max(0, tree.get_light(i)[2]-10)))

        time.sleep(1/45)

        angle = (angle + 0.1) % 6.28
        angle2 = (angle2 + 0.034) % 6.28

        tree.update()
