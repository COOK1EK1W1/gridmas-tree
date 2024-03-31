import time
import math

from util import tree

def doWanderingBall():
    height = 0.5
    angle = 0

    dist = 0.2
    radius = 0.4
    while True:
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
