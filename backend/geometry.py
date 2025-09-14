from abc import ABC, abstractmethod
from typing import Optional
from colors import Color, Pixel
from tree import tree

class Shape(ABC):
    @abstractmethod
    def does_draw(self, pixel: Pixel) -> Optional[Color]:
        ...

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

    def does_draw(self, pixel: Pixel) -> Optional[Color]:
        # Check if the pixel is within the outer bounding box
        if self.z - self.length < pixel.z < self.z + self.length and \
           self.x - self.length < pixel.x < self.x + self.length and \
           self.y - self.length < pixel.y < self.y + self.length:

            return self.color
        else:
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

    def does_draw(self, pixel: Pixel) -> Optional[Color]:
        # Check if the pixel is within the outer bounding box
        if self.z - self.length < pixel.z < self.z + self.length and \
           self.x - self.length < pixel.x < self.x + self.length and \
           self.y - self.length < pixel.y < self.y + self.length:

            return self.color
        else:
            return None


class Line(Shape):
    def __init__(self, a: tuple[float, float, float], b: tuple[float, float, float], stroke: float, color: Color):
        self.ax, self.ay, self.az = a
        self.bx, self.by, self.bz = b
        self.stroke = stroke
        self.stroke2 = stroke * stroke
        self.color = color

        # Precompute axis vector and squared length
        self.vx = self.bx - self.ax
        self.vy = self.by - self.ay
        self.vz = self.bz - self.az
        self.len2 = self.vx*self.vx + self.vy*self.vy + self.vz*self.vz

        tree._shapes.append(self)

    def does_draw(self, pixel: Pixel) -> Optional[Color]:
                # Vector from A to point
        px = pixel.x - self.ax
        py = pixel.y - self.ay
        pz = pixel.z - self.az

        # Project onto axis
        dot = px*self.vx + py*self.vy + pz*self.vz
        t = dot / self.len2 if self.len2 != 0 else 0.0

        # Reject if outside the segment
        if t < 0.0 or t > 1.0:
            return None

        # Closest point on line
        cx = self.ax + t * self.vx
        cy = self.ay + t * self.vy
        cz = self.az + t * self.vz

        dx = pixel.x - cx
        dy = pixel.y - cy
        dz = pixel.z - cz

        # Squared distance check
        if dx*dx + dy*dy + dz*dz <= self.stroke2:
            return self.color
        return None

