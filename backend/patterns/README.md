# Pattern Files

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

# Tree
the tree module keeps the active tree instance and can be imported with `from tree import tree`

## tree.set_light(n: int, color: Color)

this will update the nth light in the pixel buffer with the color

## tree.get_light(n: int) -> Color

this will return the color of the nth pixel in the pixel buffer


## tree.update()

this will update all the pixels on the tree. push the buffer to the physical pixels

update wil also self regulate to 30 fps, adding delay if the previous call was less than 33ms ago


## tree.turnOffLight(n: int)

set the nth light in the pixel buffer to black


## tree.coords: list[float, float, float]

an array of 3d coordinates of each pixel

## tree.num_pixels: int

the total number of pixels the tree has

## tree.height: float

the hieght of the tree from base to tip

## tree.distances: list[list[float]]

a 2d array of distances from one pixel to another

## tree.pixels: list[Pixel]

an array of pixel objects


## Color

the color module stores the Color class as well as helper functions for colors