# User Documentation

This is the main hub for anyone taking part in the 2025 GRIDmas Tree project. 

!!! warning "Please Note"
    The closing date for pattern submissions for the 2025 competition is: XX.YY.ZZZZ<br>
    Please make sure you have submitted your pattern **before** this date


For your first pattern, you can use this code [Taken From This Example](/samples/on):
```py
from gridmas import *

i = 0
def draw():
    global i
    for pixel in tree.pixels:
        if pixel.z < i:
            pixel.set_rgb(200, 55, 2)

    i += tree.height / 70
```

From here you can build your own pattern. 

## Pattern Requirements
To be a part of the competition, your pattern must have three things:
1. A name: your pattern must have a `name` variable that describes what your pattern does
2. An author: your pattern must have an `author` variable telling us who made it
3. Draw: A `draw` function is how the tree will show your pattern. Without one, your pattern simply will not run.

An example of this is shown below:
```py title="Example Base Pattern"
from gridmas import *
from random import randint

def draw():
    # For every frame, loop through each pixel on the tree
    for pixel in tree.pixels:
        # Set each pixel to a different RGB color
        pixel.set_rgb(randint(0, 255), randint(0, 255), randint(0, 255))
```