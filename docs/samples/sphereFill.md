# Sphere Fill

By _Ciaran_

```py linenums="1"
from particle_system import ParticleSystem, SphereParticle
from tree import tree
from colors import Color

name = "Sphere Fill"
author = "Ciaran"


class Sphere(SphereParticle):
    def __init__(self):
        super().__init__(0, 0, tree.height / 2, 0, 300, Color.random())

    def advance(self):
        self.radius += 0.01


def run():
    particle_system = ParticleSystem(tree)
    particle_system.add_particle(Sphere())

    tree.black()
    while True:
        for _ in range(100):

            particle_system.fast_draw()
            particle_system.advance()
        particle_system.add_particle(Sphere(), start=True)


if __name__ == "__main__":
    run()

```