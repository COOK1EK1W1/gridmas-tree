# Tree.sleep()

::: backend.tree.Tree.sleep

:octicons-command-palette-16: Example Usage:

``` py  
from tree import tree
from color import Color

name = "Sleep Example"
author = "Owen"

def run():
    while True:
        tree.fill(Color(255, 0, 0)) # Set the entire tree to red
        tree.update() # Push the pixels onto the tree

        tree.fill(Color(0, 0, 255)) # Set the entire tree to blue

        tree.sleep(45) # Pause the pattern for 45 frames. At default frame rate, this is 1 second

        tree.update() # Push the pixels onto the tree
```