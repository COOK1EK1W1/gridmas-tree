from typing import Callable, Optional
from util import generate_distance_map, linear, read_tree_csv
import time
from colors import Color, Pixel


class Tree():
    """This is the main way to modify the pixels on the tree.


       To use in your file, import as follows:
         from tree import tree

       After this, you can modify the pixels on the tree as such:
         def main():
           for pixel in tree.pixels:
             pixel.set_rgb(0, 0, 0)

       Attributes:
         pixels: list[Pixel]: Pixel buffer held by the tree. Gets pushed to pixel driver on every update. The arry is in the same order as the lights on the strip
         coords: list[tuple[float, float, float]]: A list of 3d coordinates (x,y,z) which is in ordeer of pixels on the strip i.e. parrallel with tree.pixels
         num_pixels: int: The number of pixels on the tree. Same as doing len(tree.pixels)
         height: float: Height of the tree
         distances: list[list[float]]: A 2d array which holds pre-computed 3D euclidean distances between all pairs of pixels. The index of each array is parrallel with tree.pixels
    """

    def __init__(self):
        pass


    def init(self, tree_file: str):
        """For internal use
        Initialise / reset the tree"""
        self.coords = read_tree_csv(tree_file)

        self.num_pixels = int(len(self.coords))

        self.height = max([x[2] for x in self.coords])

        self.distances = generate_distance_map(self.coords)

        self.pixels: list[Pixel] = [Pixel((x[0], x[1], x[2])) for x in self.coords]

        self.last_update = time.perf_counter()
        self.render_times: list[float] = []

    def request_frame(self):
        """For internal use
        return the current pixel buffer"""
        colors: list[int] = []

        # loop for every pixel and determine what color it should be
        for i in range(self.num_pixels):

            # 1. check if the pixel has been directly changed
            if self.pixels[i].changed:
                colors.append(self.pixels[i].to_int())
                self.pixels[i].changed = False
                continue

            # 2. check for objects

            # 3. check for background

            # default last color used.
            colors.append(self.pixels[i].to_int())

        return colors

    def set_light(self, n: int, color: Color):
        """Set the Nth light in the strip to the specified color

        Args:
            n (int): The light you want to set
            color (Color): The color that you want to set the light to
        """
        self.pixels[n].set_color(color)

    def get_light(self, n: int) -> Pixel:
        """Get the Nth light on the strip

        Args:
            n (int): The light you want to retrieve

        Returns:
            Pixel: The light that you have requested. You can then set the color of it directly
        """
        return self.pixels[n]

    def set_fps(self, fps: int):
        """Allows you to change the speed that you want the animation to run at.
           If unset, the default fps is 45

        Args:
            fps (int): target fps for the animation.
        """
        self.fps = fps

    def fade(self, n: float = 1.1):
        """Fade the entire tree.
           n<1 will cause the tree to become brighter.
           tree.lerp(0, 0, 0) is prefered to tree.fade() as it if more performant
           and gived better cotnrol over timing.

        Args:
            n (float, optional): Unknown. Defaults to 1.1.
        """
        for pixel in self.pixels:
            pixel.fade(n)

    def black(self):
        """Sets all pixels on the tree to black (0, 0, 0)
        """
        for pixel in self.pixels:
            pixel.set_rgb(0, 0, 0)

    def fill(self, color: Color):
        """Set all lights on the tree to one color

        Args:
            color (Color): The color you want to set the tree to
        """
        for pixel in self.pixels:
            pixel.set_color(color)

    def lerp(self, color: Color, frames: int, fn: Callable[[float], float] = linear):
        """Lerp the entire tree from its current color to the target color over the specified amount of frames

        Args:
            color (Color): Target color
            frames (int): The number of frames to perform the lerp over
            fn (Callable[[float], float], optional): Timing function from the Util module. Defaults to linear.
        """
        for pixel in self.pixels:
            pixel.lerp(color.to_tuple(), frames, fn=fn)

def pixels(a: Optional[int] = None):
    global tree
    if a is None:
        return tree.pixels
    else:
        return tree.pixels[a]

tree = Tree()
