import math
from attribute import RangeAttr

from tree import tree
from colors import Color

name = "Sphere Fill"
author = "Ciaran"


def run():
    color = Color.random()
    while True:
        center = [0, 0, tree.height / 2]  # Center of the tree

        # Radius expansion parameters
        min_radius = 0.1
        # pythagoras, distance from the centre to the edge
        max_radius = ((tree.height / 2) ** 2 + 1) ** 0.5
        expansion_speed = RangeAttr("speed", 0.05, 0.01, 0.4, 0.01)

        radius = min_radius

        while radius <= max_radius:
            for pixel in tree.pixels:
                distance_to_center = math.sqrt((pixel.x - center[0]) ** 2 + (pixel.y - center[1]) ** 2 + (pixel.z - center[2]) ** 2)

                # Check if the current LED is within the expanding sphere
                if distance_to_center <= radius:
                    pixel.set_color(color)

            # Update the tree display
            tree.update()

            # Increase the radius for the next iteration
            radius += expansion_speed.get()

        # Clear the tree after the sphere has expanded completely
        tree.update()
        color = Color.differentfrom(color)


if __name__ == "__main__":
    run()
