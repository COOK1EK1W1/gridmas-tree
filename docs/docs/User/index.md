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