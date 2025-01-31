# Tree.fill()

::: backend.tree.Tree.fill

:octicons-command-palette-16: Example Usage:

``` py  
from tree import tree
from color import Color

name = "Fill Example"
author = "Owen"

def run():
    while True:
        tree.fill(Color.blue()) # Set all pixels on the tree to blue

        tree.update() # Push the pixels onto the tree
```