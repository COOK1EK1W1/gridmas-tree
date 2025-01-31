# Tree.set_light()

::: backend.tree.Tree.sleep

:octicons-command-palette-16: Example Usage:

``` py  
from tree import tree
from color import Color

name = "Set Light Example"
author = "Owen"

def run():
    while True:
        tree.set_light(10, Color(255, 255, 0)) # Set the 10th light on the tree to orange

        tree.update() # Push the pixels onto the tree
```