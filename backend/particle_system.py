"""The particle system allows you to easily add different particles to the tree to create epic effects

This is a fairly basic particle system, the behavours of the particles are specified in a subclass,
then are added to the simulation

The particle system will then advance each particle, and then draw them to the tree
"""

from abc import ABC, abstractmethod

from colors import Color, Pixel
from util import euclidean_distance
from tree import Tree


class Particle(ABC):
    def __init__(self, x: float, y: float, z: float, max_age: int):
        self.x = x
        self.y = y
        self.z = z
        self.age = 0
        self.max_age = max_age
        self.is_dead = False

    def kill(self):
        self.is_dead = True

    @abstractmethod
    def draw(self, tree: Tree) -> None:
        ...

    def s_advance(self):
        self.age += 1
        self.advance()

    @abstractmethod
    def advance(self):
        ...

    @abstractmethod
    def fast_draw(self, pixel: Pixel) -> Color | None:
        ...


class CubeParticle(Particle):
    def __init__(self, x: float, y: float, z: float, length: float, max_age: int, color: Color):
        super().__init__(x, y, z, max_age)
        self.length = length
        self.color = color

    def draw(self, tree: Tree):
        for pixel in tree.pixels:
            # Check if the pixel is within the outer bounding box
            if self.z - self.length < pixel.z < self.z + self.length and \
               self.x - self.length < pixel.x < self.x + self.length and \
               self.y - self.length < pixel.y < self.y + self.length:

                pixel.set_color(self.color)

    @abstractmethod
    def advance(self):
        ...

    def fast_Draw(self, pixel: Pixel) -> Color | None:
        # Check if the pixel is within the outer bounding box
        if self.z - self.length < pixel.z < self.z + self.length and \
           self.x - self.length < pixel.x < self.x + self.length and \
           self.y - self.length < pixel.y < self.y + self.length:

            return self.color
        else:
            return None


class SphereParticle(Particle):
    """This is a particle of a sphere, you should sub class
       this to fill in your own advance function to add behaviour to it

    """

    def __init__(self, x: float, y: float, z: float, radius: float, max_age: int, color: Color):
        """typically when subclassing you'll use super().__init__(...) syntax

        Args:
            x (float): x position
            y (float): y position
            z (float): z position
            radius (float): Radius of the sphere
            max_age (int): The maximum age of the sphere
            color (Color): The color of the sphere
        """
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
                    if euclidean_distance([pixel.x, pixel.y, pixel.z], [self.x, self.y, self.z]) < self.radius:
                        pixel.set_color(self.color)

    @abstractmethod
    def advance(self):
        ...

    def fast_draw(self, pixel: Pixel) -> Color | None:
        inner_radius = 0.866  # sqrt(3) / 2, side length of box inscribed by sphere
        if self.z - self.radius < pixel.z < self.z + self.radius and \
           self.x - self.radius < pixel.x < self.x + self.radius and \
           self.y - self.radius < pixel.y < self.y + self.radius:

            # Check if the pixel is within the inner bounding box
            if self.z - inner_radius < pixel.z < self.z + inner_radius and \
               self.x - inner_radius < pixel.x < self.x + inner_radius and \
               self.y - inner_radius < pixel.y < self.y + inner_radius:
                return self.color
            else:
                # Perform the distance check if not within the inner bounding box
                if euclidean_distance([pixel.x, pixel.y, pixel.z], [self.x, self.y, self.z]) < self.radius:
                    return self.color


class ParticleSystem:
    """The main particle system runner
    """
    def __init__(self, tree: Tree):
        """Initiate a particle system for the tree, this should be done once within the run function

        Args:
            tree (Tree): The tree to generate a particle system for
        """
        self.tree = tree
        self._particles: list[Particle] = []

    def add_particle(self, particle: Particle, start: bool = False):
        """Add a particle to the simulation

        Args:
            particle (Particle): The particle to add to the system
            start (bool, optional): If true, the particle is added at the start of the system particle list. Defaults to False.
        """
        if start:
            self._particles.insert(0, particle)
        else:
            self._particles.append(particle)

    def advance(self):
        """This will call the advance function on all particles. But does not draw them."""
        for particle in self._particles:
            particle.s_advance()

        self._particles = list(filter(lambda x: x.age < x.max_age or not x.is_dead, self._particles))

    def draw(self) -> None:
        """Run the draw function for all particles in the system
        """
        for particle in self._particles:
            particle.draw(self.tree)

        self.tree.update()

    def fast_draw(self):
        """Better for performance if there are lots of overlapping particles. However, it could
           lead to unpredictable overlap coloring
        """
        skip_amount = 0
        for pixel in self.tree.pixels:
            for i, particle in enumerate(self._particles):
                a = particle.fast_draw(pixel)
                if a is not None:
                    pixel.set_color(a)
                    skip_amount += len(self._particles) - i
                    break
        # if len(self._particles) != 0:
            # print(skip_amount / (len(self.tree.pixels) * len(self._particles)))
        self.tree.update()
