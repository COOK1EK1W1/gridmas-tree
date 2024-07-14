from abc import ABC, abstractmethod
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
        for pixel in tree.pixels:
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
