"""Contains all the methods you need to change the tree. (Where the magic happens)"""

from abc import ABC
import numpy as np
from util import  linear, read_tree_csv
import time
from colors import Pixel
from typing import TYPE_CHECKING, Callable, Optional, TypeVar
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
        

        self._pixels: list[Pixel] = [Pixel(i, self._coords[i]) for i in range(self._num_pixels)]
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
        self._fps = 2

        self.draw_fn: Optional[Callable] = None


    def _pattern_reset(self):
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
        self._render_shapes()

        # pack the whole array at once. vectorized!
        rgb = self._rgb.astype(np.uint32, copy=False)
        packed = (rgb[:, 0] << 8) | (rgb[:, 1] << 16) | rgb[:, 2]

        changed = self._changed_arr

        if self._background:
            bg = (self._background._r << 8) | (self._background._g << 16) | self._background._b
            packed[~changed] = bg

        # Reset lerps
        self._lerp_prev[changed] = rgb[changed]
        self._lerp_step[changed] = 0

        changed[:] = False

        self._advance_all_lerps()

        self._frame += 1
        return packed


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

    def pixels(self):
        return self._pixels

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
