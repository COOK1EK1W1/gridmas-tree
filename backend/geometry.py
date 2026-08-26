"""Some helpful code for building Shapes for your patterns"""

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np
from colors import Color, Pixel
from tree import tree

class Shape(ABC):
    """Shape Contains a shape

    A shape to be used for geometry

    Args:
        ABC (abc.ABC): An abstract class
    """
    @abstractmethod
    def does_draw(self, positions: np.ndarray):
        """does_draw T.B.D

        

        Args:
            positions np.float32 ndarray, shape (num_pixels, 3): Positions of pixels on tree

        Returns:
            mask:   bool ndarray, shape (num_pixels,), True where this shape draws
            colors: uint8 ndarray, shape (num_pixels, 3), the RGB this shape would
                    set at that pixel (only meaningful where mask is True)
        """
        ...


class Sphere(Shape):
    """Sphere a 3D circle :wink:

    Represents a spherical object

    Args:
        Shape (Shape): Must be an instance of Shape
    """
    
    def __init__(self, pos: tuple[float, float, float], radius: float, color: Color):
        """__init__ Create a sphere

        Create an instance of Sphere

        Args:
            pos (tuple[float, float, float]): The center point of the sphere [x, y, z]
            radius (float): The radius of the sphere
            color (Color): The color of the sphere
        """
        self.pos = pos
        self.x, self.y, self.z = pos
        self.radius = radius
        self.radius2 = radius * radius  # store squared radius
        self.inner_radius = radius / 1.73205  # for inscribed cube
        self.color = color
        tree._shapes.append(self)

    def does_draw(self, positions: np.ndarray):
        center = np.array([self.x, self.y, self.z])
        diff = positions - center
        dist2 = np.einsum('ij,ij->i', diff, diff)
        mask = dist2 <= self.radius2
        colors = np.broadcast_to(
            np.array(self.color.to_tuple(), dtype=np.uint8), positions.shape
        )
        return mask, colors

class Box(Shape):
    def __init__(self, pos: tuple[float, float, float], length: float, color: Color):
        self.pos = pos
        self.x = pos[0]
        self.y = pos[1]
        self.z = pos[2]
        self.length = length
        self.color = color
        tree._shapes.append(self)

    def does_draw(self, positions: np.ndarray):
        center = np.array([self.x, self.y, self.z])
        diff = np.abs(positions - center)
        mask = np.all(diff < self.length, axis=1)
        colors = np.broadcast_to(
            np.array(self.color.to_tuple(), dtype=np.uint8), positions.shape
        )
        return mask, colors


class Line(Shape):
    """Line A line

    Has a starting point, end point, color, and a stroke

    Args:
        Shape (Shape): Must be an instance of Shape
    """
    def __init__(self, a: tuple[float, float, float], b: tuple[float, float, float], stroke: float, color: Color):
        """__init__ Create a line

        Create a new instance of Line

        Args:
            a (tuple[float, float, float]): The start position of the line [x, y, z]
            b (tuple[float, float, float]): The end position of the line [x, y, z]
            stroke (float): The width of the line
            color (Color): The color of the line
        """
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

    def does_draw(self, positions: np.ndarray):
        a = np.array([self.ax, self.ay, self.az])
        v = np.array([self.vx, self.vy, self.vz])

        p = positions - a
        dot = p @ v
        if self.len2 != 0:
            t = dot / self.len2
        else:
            t = np.zeros(positions.shape[0])

        in_segment = (t >= 0.0) & (t <= 1.0)

        closest = a + np.outer(t, v)
        diff = positions - closest
        dist2 = np.einsum('ij,ij->i', diff, diff)

        mask = in_segment & (dist2 <= self.stroke2)
        colors = np.broadcast_to(
            np.array(self.color.to_tuple(), dtype=np.uint8), positions.shape
        )
        return mask, colors