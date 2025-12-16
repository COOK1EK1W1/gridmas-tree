"""Contains all the methods you need to change the tree. (Where the magic happens)"""

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
        self._fps = 45

        self._color_buffer = [0]*self._num_pixels

    def _pattern_reset(self):
        self._pattern_started_at = time.time()
        self._frame = 0
        self._background = None
        self._fps = 45

    def _request_frame(self):
        """For internal use
        return the current pixel buffer"""

        # loop for every pixel and determine what color it should be
        for i in range(self._num_pixels):

            # 1. check if the pixel has been directly changed
            if self._pixels[i]._changed:
                #colors[i] = self._pixels[i].to_bit_string()
                self._color_buffer[i] = (self._pixels[i]._r << 8) | (self._pixels[i]._g << 16) | self._pixels[i]._b

                self._pixels[i]._changed = False
                self._pixels[i].lerp_reset()
                continue

            # 2. check for objects
            changed = False
            for shape in reversed(self._shapes):
                c = shape.does_draw(self._pixels[i])
                if c is not None:
                    # colors[i] = c.to_bit_string()
                    self._color_buffer[i] = (c._r << 8) | (c._g << 16) | c._b
                    self._pixels[i].set(c)
                    changed = True
                    break
            if changed:
                continue

            # 3. check for background
            if self._background:
                # colors[i] = self._background.to_bit_string()
                self._color_buffer[i] = (self._background._r << 8) | (self._background._g << 16) | self._background._b
                continue

            # default last color used.
            #colors[i] = self._pixels[i].to_bit_string()
            self._color_buffer[i] = (self._pixels[i]._r << 8) | (self._pixels[i]._g << 16) | self._pixels[i]._b

        for i in range(self._num_pixels):
            self._pixels[i].cont_lerp()

        self._shapes = []
        self._frame += 1

        return self._color_buffer


    def _generate_distance_map(self) -> list[list[float]]:
        return [ [dist(pos1, pos2) for pos2 in self._coords] for pos1 in self._coords ]

    def _generate_pixel_distances(self) -> list[list[tuple[Pixel, float]]]:
        return [ sorted( zip(self._pixels, dist_row), key=lambda x: x[1]) for dist_row in self._distances]

def height() -> float: 
    """The height of the tree

    Examples:
        if pixel.z < height() / 2:
            pixel.set_rgb(255, 255, 255)

    """
    return tree._height

def num_pixels() -> int:
    """The number of pixels, equivelant to len(pixels()) but faster"""
    return tree._num_pixels

@overload
def pixels() -> list["Pixel"]: ...
@overload
def pixels(n: int) -> "Pixel": ...

def pixels(n: Optional[int] = None) -> Union["Pixel", list["Pixel"]]:
    """The main way of accessing pixels

    Args:
        n (Optional[int]): Grab only the nth pixel

    Examples:
        for pixel in pixels():
            pixel.set_rgb(255, 255, 255)

        for i in range(num_pixels()):
            pixels(i).set_rgb(255, 255, 255)
    """
    global tree
    if n is None:
        return tree._pixels
    else:
        return tree._pixels[n]

def set_pixel(n: int, color: Color):
    """Set the Nth light in the strip to the specified color

    Args:
        n (int): The light you want to set
        color (Color): The color that you want to set the light to

    Example:
        ```
        set_pixel(2, Color.black())
        ```
    """
    pixels(n).set(color)

def set_fps(fps: int):
    """Allows you to change the speed that you want the animation to run at.
       If unset, the default fps is 45

    Args:
        fps (int): target fps for the animation.

    Example:
        ```
        set_fps(30)
        def draw():
            pass # called 30 times per second
        ```
        
    """
    tree._fps = fps

def fade(n: int = 10):
    """Fade the entire tree.
        fades the tree to black over n frames
    Args:
        n (int, optional): Unknown. Defaults to 10
    Example:
        ```
        def draw():
            fade(10)
        ```
    """
    c = Color.black()
    for pixel in tree._pixels:
        pixel.lerp(c, n)

def background(c: Color):
    """Set the background color of the tree
        if a pixel hasn't been directly set or no shape overlaps the pixel, it will be drawn as the background color.

        removes any fading or lerping that might be applying

        example:
        ```
        background(Color.black())
        def draw():
            set_pixel(1, Color.white())
        ```
    """
    tree._background = c

def fill(color: Color):
    """Set all lights on the tree to one color

    This differs from background as it is part of the 1st rendering layer, directly setting pixels

    Args:
        color (Color): The color you want to set the tree to
    """
    for pixel in tree._pixels:
        pixel.set(color)

def lerp(color: Color, frames: int, fn: Callable[[float], float] = linear):
    """Lerp the entire tree from its current color to the target color over the specified amount of frames

    Once lerp has been called, it will automatically interpolate every frame to the target. Subsequent calls with the same parameters will continue the lerp, not reset.

    Args:
        color (Color): Target color
        frames (int): The number of frames to perform the lerp over
        fn (Callable[[float], float], optional): Timing function from the Util module. Defaults to linear.

    Example:
        ```
        def draw():
            lerp(Color.black(), 10) # similar to fade
        ```
    """
    for pixel in tree._pixels:
        pixel.lerp(color, frames, fn=fn)

def coords():
    """An array of 3d coordinates mapped directly to the pixels
    coords()[10] gives the xyz tuple of the 10th pixel in the strip
    equivelant to pixels(10).xyz
    """
    return tree._coords

def sleep(n: int):
    """sleep for n frames

    example:
        ```
        def draw():
            lerp(Color.black(), 10)
            yield from sleep(10)
        ```
    """
    for _ in range(n):
        yield

def frame() -> int:
    """The current frame number since the start of the pattern
            example:
            ```
            def draw():
                f = frame() # 1, 2, 3
                print(f"{f} frames since the pattern started")
            ```
"""
    return tree._frame

def seconds() -> int:
    """The number of seconds since the start of the pattern"""
    return math.floor(time.time() - tree._pattern_started_at)

def millis() -> int:
    """The number of milliseconds since the start of the pattern

        example:
            ```
            def draw():
                s = seconds()
                m = millis()
                print(f"{s}:{m} since the pattern started")
            ```
    """
    return math.floor((time.time() - tree._pattern_started_at) * 1000)

tree = Tree()
