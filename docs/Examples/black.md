# Tree.black()

::: backend.tree.Tree.black

:octicons-command-palette-16: Example Usage:

``` py  
from tree import tree

name = "Set to black Example"
author = "Owen"

def run():
    while True:
        tree.black() # Set all pixels to black (off)

        tree.update() # Push the pixels onto the tree
```