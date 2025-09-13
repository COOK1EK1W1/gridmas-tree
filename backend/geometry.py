from abc import ABC
from typing import Optional
from colors import Color, Pixel
from tree import tree

class Shape(ABC):
    def does_draw(self, pixel: Pixel) -> Optional[Color]:
        pass

class Sphere(Shape):
    def __init__(self, pos: tuple[float, float, float], radius: float, color: Color):
        self.pos = pos
        self.x, self.y, self.z = pos
        self.radius = radius
        self.radius2 = radius * radius  # store squared radius
        self.inner_radius = radius / 1.73205  # for inscribed cube
        self.color = color
        tree._shapes.append(self)

    def does_draw(self, pixel: Pixel) -> Optional[Color]:
        dx = pixel.x - self.x
        dy = pixel.y - self.y
        dz = pixel.z - self.z

        # 1. Quick reject (outside bounding box)
        if abs(dx) > self.radius or abs(dy) > self.radius or abs(dz) > self.radius:
            return None

        # 2. Quick accept (inside inscribed cube)
        if abs(dx) <= self.inner_radius and abs(dy) <= self.inner_radius and abs(dz) <= self.inner_radius:
            return self.color

        # 3. Exact sphere check (squared distance)
        if dx*dx + dy*dy + dz*dz <= self.radius2:
            return self.color

        return None

class Box(Shape):
    def __init__(self, pos: tuple[float, float, float], length: float, color: Color):
        self.pos = pos
        self.x = pos[0]
        self.y = pos[1]
        self.z = pos[2]
        self.length = length
        self.color = color
        tree._shapes.append(self)

    def fast_Draw(self, pixel: Pixel) -> Optional[Color]:
        # Check if the pixel is within the outer bounding box
        if self.z - self.length < pixel.z < self.z + self.length and \
           self.x - self.length < pixel.x < self.x + self.length and \
           self.y - self.length < pixel.y < self.y + self.length:

            return self.color
        else:
            return None

