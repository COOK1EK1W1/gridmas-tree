import random
import time
import math

from util import tree

name = "SphereFill"
display_name = "Sphere Fill"
author = "Ciaran"


def run():
    while True:
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

        # Clear the tree after the sphere has expanded completely
        tree.update()


if __name__ == "__main__":
    run()
