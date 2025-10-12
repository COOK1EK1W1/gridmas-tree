# On

This example is a basic pattern that loops through every pixel on the tree and sets them all to the `#!python on` state

```py linenums="1" title="on.py"
from prelude import *

i = 0
def draw(): # (1)!
    global i
    for pixel in tree.pixels:
        if pixel.z < i:
            pixel.set_rgb(200, 55, 2)

    i += tree.height / 70

```

1.  You might notice the difference in patterns this year.
    Your pattern now does not have control over the tree directly. You must have a `#!python draw()` function to make your pattern run