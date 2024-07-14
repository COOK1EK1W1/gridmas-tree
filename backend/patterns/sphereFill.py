from util import pythagorasDistance

from tree import tree
from colors import Color

name = "Sphere Fill"
author = "Ciaran"


class Sphere:
    def __init__(self, maxAge: int, color: Color, x: float, y: float, z: float):
        self.maxAge = maxAge
        self.color = color
        self.age = 0
        self.x = x
        self.y = y
        self.z = z
        self.radius = 0

    def update(self):
        self.radius += 0.01
        self.age += 1


def run():
    spheres: list[Sphere] = [Sphere(100, Color.random(), 0, 0, tree.height / 2)]
    while True:
        if (len(spheres) > 4):
            spheres.pop(0)
        for _ in range(50):
            for sphere in spheres:
                for pixel in tree.pixels:
                    distance_to_center = pythagorasDistance([pixel.x, pixel.y, pixel.z], [sphere.x, sphere.y, sphere.z])
                    if distance_to_center < sphere.radius:
                        pixel.set_color(sphere.color)

                sphere.update()

            # Update the tree display
            tree.update()
        spheres.append(Sphere(100, Color.differentfrom(spheres[-1].color), 0, 0, tree.height / 2))


if __name__ == "__main__":
    run()
