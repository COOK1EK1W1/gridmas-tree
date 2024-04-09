import time
import math

from util import tree

name = "wandering_ball"
display_name = "Wandering Ball"


def run():
    height = 0.5
    angle = 0
    angle2 = 0

    dist = 0.2
    radius = 0.4
    while True:
        color = (255, 255, 255)

        center = [dist * math.sin(angle), dist * math.cos(angle), height]
        height = math.sin(angle2) + 1
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
        angle2 = (angle + 0.073) % 6.28

        tree.update()
