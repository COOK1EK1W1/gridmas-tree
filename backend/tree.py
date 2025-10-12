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
    """This is a class which holds the tree data, it shouldn't be used directly """

    def __init__(self):
        pass


    def init(self, tree_file: str):
        """For internal use
        Initialise / reset the tree"""
        
        self._coords = read_tree_csv(tree_file)
        """The coordinates of all lights on the tree"""

        self._num_pixels = int(len(self._coords))
        """The number of pixels on the tree"""

        self._height = max([x[2] for x in self._coords])
        """The height of the tree"""

        self._pixels: list[Pixel] = [Pixel(i, (x[0], x[1], x[2]), self) for i, x in enumerate(self._coords)]
        """The list of all pixels on the tree"""

        # 2d array, cols from, rows to -> dist
        self._distances = self._generate_distance_map()
        """2d array, cols from, rows to -> dist"""

        # 2d array, cols from id, rows sorted array of distance
        self._pixel_distance_matrix = self._generate_pixel_distances()
        """2d array, cols from id, rows sorted array of distance"""

        self._last_update = time.perf_counter()
        """When the last update took place"""
        
        self._render_times: list[float] = []
        """A list of the render times for frames"""

        self._pattern_started_at = time.time()
        self._frame = 0
        """The current frame that the animation is on"""

        self._shapes: list[Shape] = []
        """The list of shapes that the tree can draw"""
        
        self._background = None

    def _pattern_reset(self):
        self._pattern_started_at = time.time()
        self._frame = 0
        self._background = None

    def _request_frame(self):
        """For internal use
        return the current pixel buffer"""
        colors: list[int] = []

        # loop for every pixel and determine what color it should be
        for i in range(self._num_pixels):

            # 1. check if the pixel has been directly changed
            if self._pixels[i]._changed:
                colors.append(self._pixels[i].to_bit_string())
                self._pixels[i].changed = False
                continue

            # 2. check for objects
            changed = False
            for shape in reversed(self._shapes):
                c = shape.does_draw(self._pixels[i])
                if c is not None:
                    colors.append(c.to_bit_string())
                    self._pixels[i].set(c)
                    changed = True
                    break
            if changed:
                continue

            # 3. check for background
            if self._background:
                colors.append(self._background.to_bit_string())
                continue

            # default last color used.
            colors.append(self._pixels[i].to_bit_string())

        for i in range(self._num_pixels):
            self._pixels[i].cont_lerp()

        self._shapes = []
        self._frame += 1

        return colors

    def _generate_distance_map(self) -> list[list[float]]:
        ret: list[list[float]] = []
        for fr in self._coords:
            inter: list[float] = []
            for to in self._coords:
                inter.append(dist([x for x in fr], [x for x in to]))
            ret.append(inter)
        return ret

    def _generate_pixel_distances(self) -> list[list[tuple[Pixel, float]]]:
        ret: list[list[tuple[Pixel, float]]] = []
        for i in range(len(self._coords)):
            distances: list[tuple[Pixel, float]] = []
            for j in range(len(self._coords)):
                distances.append((self._pixels[j], self._distances[i][j]))

            ret.append(sorted(distances, key=lambda x: x[1]))
            pass

        return ret


def height():
    return tree._height

def num_pixels():
    return tree._num_pixels

def pixel_coords():
    return tree._coords

@overload
def pixels() -> list["Pixel"]: ...
@overload
def pixels(a: int) -> "Pixel": ...

def pixels(a: Optional[int] = None) -> Union["Pixel", list["Pixel"]]:
    global tree
    if a is None:
        return tree._pixels
    else:
        return tree._pixels[a]

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
    tree._fps = fps

def fade(n: int = 10):
    """Fade the entire tree.
        fades the tree to black over n frames
    Args:
        n (int, optional): Unknown. Defaults to 10
    """
    c = Color.black()
    for pixel in tree._pixels:
        pixel.lerp(c, n)

def fill(color: Color):
    """Set all lights on the tree to one color

    Args:
        color (Color): The color you want to set the tree to
    """
    for pixel in tree._pixels:
        pixel.set(color)

def lerp(color: Color, frames: int, fn: Callable[[float], float] = linear):
    """Lerp the entire tree from its current color to the target color over the specified amount of frames

    Args:
        color (Color): Target color
        frames (int): The number of frames to perform the lerp over
        fn (Callable[[float], float], optional): Timing function from the Util module. Defaults to linear.
    """
    for pixel in tree._pixels:
        pixel.lerp(color, frames, fn=fn)

def coords():
    """TODO"""
    return tree._coords

def num_pixels():
    """TODO"""
    return tree._num_pixels



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
