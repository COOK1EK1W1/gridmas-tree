# User Documentation

This is the main hub for anyone taking part in the 2025 GRIDmas Tree project. 

!!! warning "Please Note"
    The closing date for pattern submissions for the 2025 competition is: 14/12/2025<br>
    Please make sure you have submitted your pattern **before** this date


For your first pattern, you can use this code [Taken From This Example](/samples/on):
```py title="Example - On" linenums="1"
from gridmas import *

i = 0
def draw():
    global i
    for pixel in pixels():
        if pixel.z < i:
            pixel.set_rgb(200, 55, 2)

    i += height() / 70
```

From here you can build your own pattern. 

## Pattern Requirements
For a pattern to be valid, it must do have at miminum, these two lines of code:

1. `#!python from gridmas import *` - This imports all the important things from the Gridmas module. Allowing you to manipulate the tree
2. `#!python def draw(): pass` - Obviously replacing `#!python pass` with the code you want to use to make the tree do things. This method is how your pattern is run by the pattern manager. 

!!! danger "Warning"
    If you took part in the competition last year, please not that the way your pattern is run has changed. Your pattern no longer has control over the tree. The tree has control over your pattern.

An example of this is shown below. It is the simplest pattern, it simply turns on all LEDs on the tree to a random color.

```py linenums="1"
from gridmas import *
from random import randint

def draw():
    # For every frame, loop through each pixel on the tree
    for pixel in pixels():
        # Set each pixel to a different RGB color
        pixel.set_rgb(randint(0, 255), randint(0, 255), randint(0, 255))
```

## Draw function

The rendering pipeline has been heavily optimised to allow for complex patterns with lots of shapes.

The standard frame rate is 45fps (~22ms) which is a balance between the limitations of the Raspberry pi and looking smooth on the tree. To achieve this your pattern file's `#!python draw()` function is called ever 22ms.

```py linenums="1"
def draw()
    print("I'm being called every 22ms")
```

Once the draw() function finishes, the tree is drawn to automatically. However this causes some complications, variables must be declared as global to persist between calls

```py linenums="1"
a = 0
def draw():
    global a
    a += 1
    # function is finished, draw the tree now
```

Alternatively you can use the yield syntax. Yielding pauses the execution of your pattern and allows gridmas to draw the tree.
```py linenums="1"
def draw():
    a = 0
    while True:
        a += 1
        yield # I draw the tree every 22ms
```
!!!note 
    you can use the `yield from` syntax to allow yielding from other functions, this must be bubbled down to the draw function

## Rendering pipeline

The renderer follows a simple checklist for every pixel to decide its color:

1. has the pixel been directly set. `#!python pixel(n).set_color(Color.red())`
2. Do any of the shapes contain this pixel. `#!python Sphere(...)` or `#!python Line(...)`
3. Is there a background color. `#!python background(Color.red())`
4. Leave the pixel the same as the last frame

This means Shapes are drawn on top of the background, and directly setting colors is drawn on top of shapes. 

Within each layer a function can be called several times, ie. setting the same pixel to several different colors will take the last color:

```py linenums="1"
background(Color.black())
def draw():
    background(Color.red())
    pixels(0).set_color(Color.red())
    pixels(0).set_color(Color.blue())
    pixels(0).set_color(Color.green())

# draws a green pixel and the rest red
```
