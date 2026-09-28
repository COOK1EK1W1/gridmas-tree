"""Contains all the methods you need to change the tree. (Where the magic happens)"""

import math
from abc import ABC
from types import GeneratorType
import numpy as np
from typing import Callable, Generator, Optional, TypeVar, Union, overload
from util import  linear, read_tree_csv
import time
from colors import Color, Pixel
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from geometry import Shape


class Fixture(ABC):
    """This is a class which holds the tree data, it shouldn't be used directly """


    def __init__(self, coords: list[tuple[float, float, float]]):
        """For internal use
        Initialise / reset the tree"""
        
        self._coords = coords
        """The coordinates of all lights on the tree"""

        self._num_pixels = int(len(self._coords))
        """The number of pixels on the tree"""

        self._positions = np.array(self._coords, dtype=np.float32)
        self._angle     = np.arctan2(self._positions[:, 1], self._positions[:, 0])
        self._pdist     = np.sqrt(self._positions[:, 0]**2 + self._positions[:, 1]**2)
        self._rgb       = np.zeros((self._num_pixels, 3), dtype=np.uint8)
        self._changed_arr = np.zeros(self._num_pixels, dtype=bool)

        # lerp state array
        self._lerp_prev   = np.zeros((self._num_pixels, 3), dtype=np.float64)
        self._lerp_target = np.zeros((self._num_pixels, 3), dtype=np.float64)
        self._lerp_step   = np.zeros(self._num_pixels, dtype=np.int32)
        self._lerp_total  = np.zeros(self._num_pixels, dtype=np.int32)

        # lerp function stored for entire tree, not per pixel
        # this limits the tree to a single lerp function at once
        # but improves performance a lot
        self._lerp_fn = linear
        

        self._pixels: list[Pixel] = [Pixel(i, self) for i in range(self._num_pixels)]
        """The list of all pixels on the tree"""


        self._height = float(self._positions[:, 2].max())
        """The height of the tree"""

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

        self._draw_fn: Optional[Callable[[], Optional[Generator[None, None, None]]]] = None
        self._draw_generator = None


    def set_draw_fn(self, draw_fn: Optional[Callable[[], Optional[Generator[None, None, None]]]]):
        if self._draw_fn == draw_fn:
            return
        self._draw_fn = draw_fn
        self._draw_generator = None

        self._pattern_started_at = time.time()
        self._frame = 0
        self._background = None
        self._fps = 45

    def _render_shapes(self):
        if len(self._shapes) == 0: return

        undetermined = np.ones(self._num_pixels, dtype=bool)

        for shape in reversed(self._shapes):
            if not np.any(undetermined):
                break

            draw_mask, colors = shape.does_draw(self._positions)
            apply_mask = undetermined & draw_mask
            if np.any(apply_mask):
                self._rgb[apply_mask] = colors[apply_mask]
                self._changed_arr[apply_mask] = True
                undetermined &= ~apply_mask

        self._shapes = []


    def _request_frame(self):
        setActiveFixture(self)
        if self._draw_generator is not None:
            try:
                next(self._draw_generator)
            except StopIteration:
                self._draw_generator = None
        if self._draw_generator is None:
            ret = self._draw_fn()
            if isinstance(ret, GeneratorType):
                self._draw_generator = ret
        self._render_shapes()

        # pack the whole array at once. vectorized!
        rgb = self._rgb.astype(np.uint32, copy=False)

        changed = self._changed_arr

        if self._background:
            rgb[~changed] = self._background

        # Reset lerps
        self._lerp_prev[changed] = rgb[changed]
        self._lerp_step[changed] = 0

        changed[:] = False

        self._advance_all_lerps()

        self._frame += 1
        setActiveFixture(None)
        return rgb


    def _advance_all_lerps(self):
        """Vectorized equivalent of calling cont_lerp() on every pixel.

        Mirrors Color.cont_lerp()
        """
        active = self._lerp_step < self._lerp_total
        if not np.any(active):
            return


        idx = np.nonzero(active)[0]
        self._lerp_step[idx] += 1

        step = self._lerp_step[idx].astype(np.float64)
        total = self._lerp_total[idx].astype(np.float64)

        t = np.divide(step, total, out=np.ones_like(step), where=total != 0)
        t = np.clip(t, 0.0, 1.0)

        eased = self._lerp_fn(t)[:, None]

        self._rgb[idx] = np.clip(
            (self._lerp_prev[idx] + (self._lerp_target[idx] - self._lerp_prev[idx]) * eased), 
            0,
            255,
        ).astype(np.uint8)


    def _generate_distance_map(self) -> np.ndarray:
        positions = self._positions.astype(np.float64, copy=False)
        diff = positions[:, None, :] - positions[None, :, :]
        return np.sqrt(np.einsum('ijk,ijk->ij', diff, diff))

    def _generate_pixel_distances(self) -> list[list[tuple[Pixel, float]]]:
        order = np.argsort(self._distances, axis=1, kind="stable")
        sorted_dists = np.take_along_axis(self._distances, order, axis=1)

        pixels_arr = np.array(self._pixels, dtype=object)
        sorted_pixels = pixels_arr[order]

        return [
            list(zip(sorted_pixels[i], sorted_dists[i]))
            for i in range(self._num_pixels)
        ]


_active_fixture: Optional[Fixture] = None
def setActiveFixture(fixture: Optional[Fixture]):
    global _active_fixture
    _active_fixture = fixture

def get_active_fixture():
    return _active_fixture



V = TypeVar('V', bound='Volume')
class Volume(Fixture):

    def __init__(self, coords: list[tuple[float, float, float]]):
        super().__init__(coords)


    @classmethod
    def from_csv(cls: type[V], path: str) -> V:
        return cls(read_tree_csv(path))

    @classmethod
    def from_grid(cls: type[V], dim: tuple[int, int, int], pitch: float) -> V:
        ...

W = TypeVar('W', bound='Wall')
class Wall(Fixture):
    @classmethod
    def from_csv(cls: type[W], path: str) -> W:
        return cls(read_tree_csv(path))

    @classmethod
    def from_grid(cls: type[W], dim: tuple[int, int], pitch: float) -> W:
        ...


E = TypeVar('E', bound='Graph')
class Graph(Fixture):
    @classmethod
    def from_csv(cls: type[E], b: str) -> E:
        ...

class CompoundFixture(Fixture):
    def add(self, f: Fixture, name: str):
        ...


def height() -> float: 
    """The height of the tree

    Examples:
        if pixel.z < height() / 2:
            pixel.set_rgb(255, 255, 255)

    """
    return get_active_fixture()._height

def num_pixels() -> int:
    """The number of pixels, equivelant to len(pixels()) but faster"""
    return get_active_fixture()._num_pixels

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
    if n is None:
        return get_active_fixture()._pixels
    else:
        return get_active_fixture()._pixels[n]

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
    get_active_fixture()._rgb[n][0] = color._r
    get_active_fixture()._rgb[n][1] = color._g
    get_active_fixture()._rgb[n][2] = color._b

    get_active_fixture()._changed_arr[n] = True


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
    get_active_fixture()._fps = fps


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
    lerp(c, n)


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
    get_active_fixture()._background = c


def fill(color: Color):
    """Set all lights on the tree to one color

    This differs from background as it is part of the 1st rendering layer, directly setting pixels

    Args:
        color (Color): The color you want to set the tree to
    """
    get_active_fixture()._rgb[:] = color.to_tuple()
    get_active_fixture()._changed_arr[:] = True


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
    target = np.asarray(color.to_tuple(), dtype=np.uint8)

    changed = (
        np.any(get_active_fixture()._lerp_target != target, axis=1)
        | (get_active_fixture()._lerp_total != frames)
    )

    if not np.any(changed):
        return

    # Save the current RGB values as the interpolation starting point.
    get_active_fixture()._lerp_prev[changed] = _active_fixture._rgb[changed]

    # Reset interpolation progress.
    get_active_fixture()._lerp_step[changed] = 0

    # Set new interpolation state.
    get_active_fixture()._lerp_target[changed] = target
    get_active_fixture()._lerp_total[changed] = frames
    get_active_fixture()._lerp_fn = fn


def coords():
    """An array of 3d coordinates mapped directly to the pixels
    coords()[10] gives the xyz tuple of the 10th pixel in the strip
    equivelant to pixels(10).xyz
    """
    return get_active_fixture()._coords

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
    return get_active_fixture()._frame

def seconds() -> int:
    """The number of seconds since the start of the pattern"""
    return math.floor(time.time() - get_active_fixture()._pattern_started_at)

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
    return math.floor((time.time() - get_active_fixture()._pattern_started_at) * 1000)


def _rotated_z(theta: float, alpha: float) -> np.ndarray:
    """Compute the rotated Z coordinate for every pixel at once.
    Helper function for wipe() functions
    Args:
        theta (float): Angle in radians
        alpha (float): Angle in radians
    Returns:
        np.ndarray: An (N,) array of rotated Z values, one per pixel, in the
            same order as coords()/pixels()
    """
    xyz = np.asarray(coords(), dtype=np.float64)
    x, y, z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    return np.sin(theta) * (x * np.sin(alpha) + y * np.cos(alpha)) + z * np.cos(theta)


def _set_masked(mask: np.ndarray, color: Color) -> None:
    """Vectorised equivalent of `[set_pixel(i, color) for i in idx]`.
    Directly writes the color into the tree's underlying rgb array for every
    pixel where mask is True, and flags those pixels as changed.
    Args:
        mask (np.ndarray): An (N,) boolean array, True where the pixel should be set
        color (Color): The color to set the masked pixels to
    """
    if not np.any(mask):
        return

    rgb = np.asarray(color.to_tuple(), dtype=np.uint8)
    get_active_fixture()._rgb[mask] = rgb
    get_active_fixture()._changed_arr[mask] = True


def _lerp_masked(mask: np.ndarray, color: Color, frames: int, fn: Callable[[float], float] = linear) -> None:
    """Vectorised equivalent of `[pixels(i).lerp(color, frames, fn=fn) for i in idx]`.
    Mirrors tree.py's module level lerp(), but scoped to only the pixels selected by mask
    instead of the whole tree. Only (re)starts the interpolation for pixels whose target/duration
    actually changed, matching Color.set_lerp()'s no-op-if-unchanged behaviour.
    Args:
        mask (np.ndarray): An (N,) boolean array, True where the pixel should start/continue lerping
        color (Color): The target color to lerp to
        frames (int): The number of frames to lerp over
        fn (Callable[[float], float], optional): Timing function from the Util module. Defaults to linear.
    """
    if not np.any(mask):
        return

    target = np.asarray(color.to_tuple(), dtype=np.uint8)

    changed = mask & (
        np.any(get_active_fixture()._lerp_target != target, axis=1)
        | (get_active_fixture()._lerp_total != frames)
    )

    if not np.any(changed):
        return

    get_active_fixture()._lerp_prev[changed] = get_active_fixture()._rgb[changed]
    get_active_fixture()._lerp_step[changed] = 0
    get_active_fixture()._lerp_target[changed] = target
    get_active_fixture()._lerp_total[changed] = frames
    get_active_fixture()._lerp_fn = fn


def _cont_lerp_masked(mask: np.ndarray) -> None:
    """Vectorised equivalent of `[pixels(i).cont_lerp() for i in idx]`.
    Mirrors tree.py's Tree._advance_all_lerps(), but scoped to only the pixels
    selected by mask instead of every pixel on the tree.
    Args:
        mask (np.ndarray): An (N,) boolean array, True where the pixel's lerp should advance one step
    """
    active = mask & (get_active_fixture()._lerp_step < _active_fixture._lerp_total)
    if not np.any(active):
        return

    idx = np.flatnonzero(active)
    get_active_fixture()._lerp_step[idx] += 1

    step = get_active_fixture()._lerp_step[idx].astype(np.float64)
    total = get_active_fixture()._lerp_total[idx].astype(np.float64)

    t = np.divide(step, total, out=np.ones_like(step), where=total != 0)
    t = np.clip(t, 0.0, 1.0)

    eased = get_active_fixture()._lerp_fn(t)[:, None]

    get_active_fixture()._rgb[idx] = np.clip(
        (get_active_fixture()._lerp_prev[idx] + (_active_fixture._lerp_target[idx] - _active_fixture._lerp_prev[idx]) * eased),
        0,
        255,
    ).astype(np.uint8)
