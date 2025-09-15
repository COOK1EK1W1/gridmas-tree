from math import dist
import math
from typing import Callable, Optional, Union, overload
from util import  linear, read_tree_csv
import time
from colors import Color, Pixel
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from geometry import Shape


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

        self.pixels: list[Pixel] = [Pixel(i, (x[0], x[1], x[2]), self) for i, x in enumerate(self.coords)]

        # 2d array, cols from, rows to -> dist
        self.distances = self._generate_distance_map()

        # 2d array, cols from id, rows sorted array of distance
        self.pixel_distance_matrix = self._generate_pixel_distances()

        self.last_update = time.perf_counter()
        self.render_times: list[float] = []

        self.pattern_started_at = time.time()
        self.frame = 0

        self._shapes: list[Shape] = []
        self._background = None

    def _pattern_reset(self):
        self.pattern_started_at = time.time()
        self.frame = 0
        self._background = None

    def request_frame(self):
        """For internal use
        return the current pixel buffer"""
        colors: list[int] = []

        # loop for every pixel and determine what color it should be
        for i in range(self.num_pixels):

            # 1. check if the pixel has been directly changed
            if self.pixels[i]._changed:
                colors.append(self.pixels[i].to_bit_string())
                self.pixels[i].changed = False
                continue

            # 2. check for objects
            changed = False
            for shape in reversed(self._shapes):
                c = shape.does_draw(self.pixels[i])
                if c is not None:
                    colors.append(c.to_bit_string())
                    self.pixels[i].set(c)
                    changed = True
                    break
            if changed:
                continue

            # 3. check for background
            if self._background:
                colors.append(self._background.to_bit_string())
                continue

            # default last color used.
            colors.append(self.pixels[i].to_bit_string())

        for i in range(self.num_pixels):
            self.pixels[i].cont_lerp()

        self._shapes = []
        self.frame += 1

        return colors

    def set_light(self, n: int, color: Color):
        """Set the Nth light in the strip to the specified color

        Args:
            n (int): The light you want to set
            color (Color): The color that you want to set the light to
        """
        self.pixels[n].set(color)

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

    def fade(self, n: int = 10):
        """Fade the entire tree.
            fades the tree to black over n frames
        Args:
            n (int, optional): Unknown. Defaults to 10
        """
        c = Color.black()
        for pixel in self.pixels:
            pixel.lerp(c, n)

    def fill(self, color: Color):
        """Set all lights on the tree to one color

        Args:
            color (Color): The color you want to set the tree to
        """
        for pixel in self.pixels:
            pixel.set(color)

    def lerp(self, color: Color, frames: int, fn: Callable[[float], float] = linear):
        """Lerp the entire tree from its current color to the target color over the specified amount of frames

        Args:
            color (Color): Target color
            frames (int): The number of frames to perform the lerp over
            fn (Callable[[float], float], optional): Timing function from the Util module. Defaults to linear.
        """
        for pixel in self.pixels:
            pixel.lerp(color, frames, fn=fn)

    def _generate_distance_map(self) -> list[list[float]]:
        ret: list[list[float]] = []
        for fr in self.coords:
            inter: list[float] = []
            for to in self.coords:
                inter.append(dist([x for x in fr], [x for x in to]))
            ret.append(inter)
        return ret

    def _generate_pixel_distances(self) -> list[list[tuple[Pixel, float]]]:
        ret: list[list[tuple[Pixel, float]]] = []
        for i in range(len(self.coords)):
            distances: list[tuple[Pixel, float]] = []
            for j in range(len(self.coords)):
                distances.append((self.pixels[j], self.distances[i][j]))

            ret.append(sorted(distances, key=lambda x: x[1]))
            pass

        return ret


def tree_height():
    return tree.height

def num_pixels():
    return tree.num_pixels

def pixel_coords():
    return tree.coords

@overload
def pixels() -> list["Pixel"]: ...
@overload
def pixels(a: int) -> "Pixel": ...

def pixels(a: Optional[int] = None) -> Union["Pixel", list["Pixel"]]:
    global tree
    if a is None:
        return tree.pixels
    else:
        return tree.pixels[a]

def set_pixel(n: int, color: Color):
    """Set the Nth light in the strip to the specified color

    Args:
        n (int): The light you want to set
        color (Color): The color that you want to set the light to
    """
    pixels(n).set(color)

def set_fps(fps: int):
    """Allows you to change the speed that you want the animation to run at.
       If unset, the default fps is 45

    Args:
        fps (int): target fps for the animation.
    """
    tree.fps = fps

def fade(n: int = 10):
    """Fade the entire tree.
        fades the tree to black over n frames
    Args:
        n (int, optional): Unknown. Defaults to 10
    """
    c = Color.black()
    for pixel in tree.pixels:
        pixel.lerp(c, n)

def fill(color: Color):
    """Set all lights on the tree to one color

    Args:
        color (Color): The color you want to set the tree to
    """
    for pixel in tree.pixels:
        pixel.set(color)

def lerp(color: Color, frames: int, fn: Callable[[float], float] = linear):
    """Lerp the entire tree from its current color to the target color over the specified amount of frames

    Args:
        color (Color): Target color
        frames (int): The number of frames to perform the lerp over
        fn (Callable[[float], float], optional): Timing function from the Util module. Defaults to linear.
    """
    for pixel in tree.pixels:
        pixel.lerp(color, frames, fn=fn)



def sleep(n: int):
    """sleep for n frames"""
    for _ in range(n):
        yield

def frame() -> int:
    """The current frame number since the start of the pattern"""
    return tree.frame

def seconds():
    """The number of seconds since the start of the pattern"""
    return math.floor(time.time() - tree.pattern_started_at)

def millis():
    """The number of milli seconds since the start of the pattern"""
    return math.floor((time.time() - tree.pattern_started_at) * 1000)

def background(c: Color):
    """Set the background color of the tree"""
    tree._background = c

tree = Tree()
