# Writing a Gridmas-tree Pattern

### Requirements
Each Pattern file is required to have an author variable and a name variable such as:


```
name = "my excelent pattern"  
author = "Ciaran"
```

Each file also requires a `run` function where the code for the pattern is stored

```
def run():
  print("my pattern is running")
```


# Module tree

# class Tree
the tree module keeps the active tree instance and can be imported with `from tree import tree`

## Methods

### set_light(n: int, color: Color)
this will update the nth light in the pixel buffer with the color

### get_light(n: int) -> Color
this will return the color of the nth pixel in the pixel buffer

### update()
this will update all the pixels on the tree. push the buffer to the physical pixels
update wil also self regulate to 45 fps, adding delay if the previous call was less than 22ms ago

## Attributes
### coords: list[float, float, float]
an array of 3d coordinates of each pixel

### num_pixels: int
the total number of pixels the tree has

### height: float
the hieght of the tree from base to tip

### distances: list[list[float]]
a 2d array of distances from one pixel to another

### pixels: list[Pixel]
an array of pixel objects


# module colors

# class Color
the Color class can be imported from colors such as `from colors import Color`

## methods
### constructor: Color(r: int, g: int, b: int) -> Color
create a color instance with rgb values, values should be between 0 and 255 inclusive

### set_RGB(r: int, g: int, b: int)
update the color of the instance

### set_color(color: Color)
update the color of the instance to another color

### fade(n)
fade the color by n, passing 1 will remain constant, anything greater than 1 will fade, less than 1 will lighten, default 1.1

### toHex() -> str
convert the color to hex string

### toTuple() -> tuple[int, int, int] 
convert the color into the rgb components in a tuple

### lerp(target: tuple[int, int, int], time: int)
linearly fade to the target color over `time` calls, the time step is advanced every call made. If the target changes the internal timer will reset and take `time` many calls to reach the new target.

## static methods

### fromHex(s: str) -> Color
### fromHSL(h: float, s: float, l: float) -> Color
### white() -> Color
### black() -> Color
### red() -> Color
### green() -> Color
### blue() -> Color
### random() -> Color
### differentfrom(color: Color) -> Color
generate a different color from the passed color

# class Pixel extends Color
Pixel extends Color and so inherits all the properties, attributes and methods of colors. it is also found in the colors module

## Attributes
### x: float
### y: float
### z: float
the 3D coordinates of the pixel in space, where z is the vertical component ranging 0 to tree.height, x is left to right ranging -1 to 1 when the tree is viewed from the front, and y comes towards the viewer facing the front ranging -1 to 1

### a: float
### d: float
these are the polar coordinates of the pixel from the center line (Z axis or "trunk" of the tree), where pixel.a is the angle and pixel.d is the distance. these combined with pixel.z gives you the 3D location.


# module util

# def euclidean_distance(a: list[float], b: list[float]) -> float (util)
calculate the euclidean distances between to n dimensional points


# module attribute
attributes the ability to change parameters of a pattern in real time from the webserver
to use, call the constructors straight after the `def main():` line of your pattern.

# class RangeAttr
## methods
### Constructor RangeAttr(name: str, value: float, min: float, max: float, step: float)
create a range attribute
### get() -> float
access the value of the attribute
### set(n: float)
set the value of the attribute

# class ColorAttr
## methods
### Constructor RangeAttr(name: str, value: Color)
create a color attribute
### get() -> color
access the value of the attribute
### set(c: Color)
set the value of the attribute


# module particle_system
a rudimentary implementation of a particle system
please don't go crazy on the amount of particles, remember this needs to run on a raspberry pi

# class ParticleSystem
## methods
### constructor ParticleSystem(tree: Tree)
construct the particle system straight after the `def main():` line in your pattern.

### add_particle(particle: Particle, start: bool = False)
add a particle to the system, start param is whether you want it at the start or end of the render, particles at the start will be rendered first

### advance()
step each particle along in time

### draw()
draw all the particles on the tree, including a tree.update()

### fast_draw()
optimise the rendering for better performance

# abstract class SphereParticle extends Particle
this needs to be subclassed to implement all the necessary details
## methods
### Constructor SphereParticle(x: float, y: float, z: float, radius: float, max_age: float, color: Color)
call this from subclass

### abstract advance()
override this method with your code to advance the particle


# Examples
```
# Sherefill.py
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
```

```
# chemplanes.py
import random
import math
from attribute import RangeAttr
from colors import Color

from tree import tree

name = "Chem planes"
author = "Ciaran"
# based on Matt Parkers Xmas tree


def run():
    color = Color(255, 255, 0)
    speed = RangeAttr("speed", 10, 1, 20, 1)
    while True:
        coords2 = [[x, y, z] for [x, y, z] in tree.coords]
        theta = random.uniform(0, 6.28)
        alpha = random.uniform(0, 6.28)
        for i, coord in enumerate(tree.coords):
            coords2[i][2] = math.sin(theta) * (coord[0] * math.sin(alpha) + coord[1] * math.cos(alpha)) + coord[2] * math.cos(theta)

        minZ = min([x[2] for x in coords2])
        maxZ = max([x[2] for x in coords2])

        color = Color.differentfrom(color)

        for rng in range(int(minZ * 200 - 10), int(maxZ * 200 + 10), max(1, int(speed.get()))):
            for i, coord in enumerate(coords2):
                if rng <= coord[2] * 200 < rng + 10:
                    tree.set_light(i, color)
                else:
                    tree.get_light(i).fade()
            tree.update()
```
