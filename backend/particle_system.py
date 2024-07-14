from abc import ABC, abstractmethod
import time
from colors import Color
from util import pythagorasDistance
from tree import Tree


class Particle(ABC):
    def __init__(self, x: float, y: float, z: float, max_age: int):
        self.x = x
        self.y = y
        self.z = z
        self.age = 0
        self.max_age = max_age
        self.is_dead = False

    @abstractmethod
    def draw(self, tree: Tree) -> None:
        ...

    def _advance(self):
        self.age += 1
        self.advance()

    @abstractmethod
    def advance(self):
        ...


class SphereParticle(Particle):
    def __init__(self, x: float, y: float, z: float, radius: float, max_age: int, color: Color):
        super().__init__(x, y, z, max_age)
        self.radius = radius
        self.color = color

    def draw(self, tree: Tree):
        inner_radius = 0.866  # sqrt(3) / 2, side length of box inscribed by sphere
        for pixel in tree.pixels:
            # Check if the pixel is within the outer bounding box
            if self.z - self.radius < pixel.z < self.z + self.radius and \
               self.x - self.radius < pixel.x < self.x + self.radius and \
               self.y - self.radius < pixel.y < self.y + self.radius:

                # Check if the pixel is within the inner bounding box
                if self.z - inner_radius < pixel.z < self.z + inner_radius and \
                   self.x - inner_radius < pixel.x < self.x + inner_radius and \
                   self.y - inner_radius < pixel.y < self.y + inner_radius:
                    pixel.set_color(self.color)
                else:
                    # Perform the distance check if not within the inner bounding box
                    if pythagorasDistance([pixel.x, pixel.y, pixel.z], [self.x, self.y, self.z]) < self.radius:
                        pixel.set_color(self.color)

    @abstractmethod
    def advance(self):
        ...


class ParticleSystem:
    def __init__(self, tree: Tree):
        self.tree = tree
        self._particles: list[Particle] = []

    def add_particle(self, particle: Particle):
        self._particles.append(particle)

    def advance(self):
        for particle in self._particles:
            particle._advance()

        self._particles = list(filter(lambda x: x.age < x.max_age or not x.is_dead, self._particles))

    def drawParticles(self) -> None:
        for particle in self._particles:
            particle.draw(self.tree)

        self.tree.update()
