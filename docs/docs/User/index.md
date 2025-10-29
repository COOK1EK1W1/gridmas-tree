# User Documentation

This is the main hub for anyone taking part in the 2025 GRIDmas Tree project. 

!!! warning "Please Note"
    The closing date for pattern submissions for the 2025 competition is: XX.YY.ZZZZ<br>
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

    i += tree.height / 70
```

From here you can build your own pattern. 

## Pattern Requirements
For a pattern to be valid, it must do have at miminum, these two lines of code:

1. `#!python from gridmas import *` - This imports all the important things from the Gridmas module. Allowing you to manipulate the tree
2. `#!python def draw(): pass` - Obviously replacing `#!python pass` with the code you want to use to make the tree do things. This method is how your pattern is run by the pattern manager. 

!!! danger "Warning"
    If you took part in the competition last year, please not that the way your pattern is run has changed. Your pattern no longer has control over the tree. The tree has control over your pattern. Try not to use a `#!python while True:...` loop in your pattern as this will make the tree unhappy with you.

An example of this is shown below. It is the simplest pattern, it simply turns on all LEDs on the tree to a random color.

```py title="Example Base Pattern" linenums="1"
from gridmas import *
from random import randint

def draw():
    # For every frame, loop through each pixel on the tree
    for pixel in pixels():
        # Set each pixel to a different RGB color
        pixel.set_rgb(randint(0, 255), randint(0, 255), randint(0, 255))
```