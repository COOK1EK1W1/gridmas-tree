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


class Clock:
    """Where one scope (a fixture's draw() or a display's display_update()) is on the presentation timeline.

    Times are the wall-clock moments frames will be *displayed*, computed
    speculatively from the shared show epoch / start of pattern, never read from time.time().
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.frame = 0
        self.started_at: Optional[float] = None
        self.frame_time: Optional[float] = None

    def begin_frame(self, t: float):
        """Enter the frame that will be displayed at unix time t"""
        if self.started_at is None:
            self.started_at = t
        self.frame_time = t

    def end_frame(self):
        self.frame += 1

    def elapsed(self) -> float:
        """Seconds between this scope's first frame and the current frame"""
        if self.frame_time is None or self.started_at is None:
            return 0.0
        return self.frame_time - self.started_at


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

        self._clock = Clock()
        """The frame count and presentation time of the running draw()"""

        self._fps = 45

        self._shapes: list[Shape] = []
        """The list of shapes that the tree can draw"""

        self._background: Optional[Color] = None

        self._draw_fn: Optional[Callable[[], Optional[Generator[None, None, None]]]] = None
        self._draw_generator = None


    def set_draw_fn(self, draw_fn: Optional[Callable[[], Optional[Generator[None, None, None]]]]):
        """set_draw_fn Reset the currently running pattern

        Resets all the runtime data of a pattern.
        Restarts the pattern's clock (its next frame is frame 0 at 0 seconds) and clears the background.
        """
        if self._draw_fn == draw_fn:
            return
        self._draw_fn = draw_fn
        self._draw_generator = None

        self._clock.reset()
        self._background = None

    def _render_shapes(self):
        """_render_shapes Renders all shapes that are currently in use

        If no shapes are present, this function immediately returns.
        If there are shapes, reverse the list and draw them to the tree
        """
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


    def _request_frame(self, t: float):
        """Render the frame that will be displayed at unix time t"""
        self._clock.begin_frame(t)
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
            rgb[~changed] = self._background.to_tuple()

        # Reset lerps
        self._lerp_prev[changed] = rgb[changed]
        self._lerp_step[changed] = 0

        changed[:] = False

        self._advance_all_lerps()

        self._clock.end_frame()
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
_active_clock: Optional[Clock] = None
def setActiveFixture(fixture: Optional[Fixture]):
    global _active_fixture, _active_clock
    _active_fixture = fixture
    _active_clock = fixture._clock if fixture is not None else None

def set_active_clock(clock: Optional[Clock]):
    """Make frame()/seconds()/millis() read from clock, used while running display_update()"""
    global _active_clock
    _active_clock = clock

def get_active_fixture():
    return _active_fixture



V = TypeVar('V', bound='Volume')
class Volume(Fixture):

    def __init__(self, coords: list[tuple[float, float, float]]):
        super().__init__(coords)


    @classmethod
    def from_csv(cls: type[V], path: str) -> V:
        return cls(read_tree_csv(path)[0])

W = TypeVar('W', bound='Wall')
class Wall(Fixture):
    @classmethod
    def from_csv(cls: type[W], path: str) -> W:
        return cls(read_tree_csv(path)[0])


class Vertex:
    """A point where edges of a Graph meet, like a corner of the house or the end of a wire.

    Don't make these yourself, get them from `vertices()` or from an Edge. Treat the
    attributes as read only, they're shared by every pattern on the fixture.

    Attributes:
        id (int): The vertex's index, `vertices(vertex.id) is vertex`
        position (np.ndarray): The (x, y, z) position of the vertex
        pixels (list[Pixel]): The pixels sitting at this vertex, often there are none
        indices (np.ndarray): The LED indices of `pixels`, for numpy
        edges (list[Edge]): Every edge with an end at this vertex
    """

    __slots__ = ("id", "position", "pixels", "indices", "edges")

    def __init__(self, id: int, position: tuple[float, float, float], pixels: list[Pixel]):
        self.id = id
        self.position = np.array(position, dtype=np.float64)
        self.pixels = pixels
        self.indices = np.array([p.id for p in pixels], dtype=np.intp)
        self.edges: list["Edge"] = []

    @property
    def x(self) -> float:
        """The x position of the vertex"""
        return float(self.position[0])

    @property
    def y(self) -> float:
        """The y position of the vertex"""
        return float(self.position[1])

    @property
    def z(self) -> float:
        """The z position of the vertex"""
        return float(self.position[2])

    @property
    def degree(self) -> int:
        """How many edges meet here, 1 is a dead end, 3 or more is a junction"""
        return len(self.edges)

    @property
    def neighbours(self) -> list["Vertex"]:
        """The vertices at the other end of each of this vertex's edges, in the same order as `edges`"""
        return [e.other(self) for e in self.edges]

    def __repr__(self) -> str:
        return f"Vertex({self.id}, pixels={self.indices.tolist()}, edges={[e.id for e in self.edges]})"


class Edge:
    """A run of pixels along a wire between two vertices.

    Don't make these yourself, get them from `edges()` or from a Vertex. Treat the
    attributes as read only, they're shared by every pattern on the fixture.

    An edge is a sequence of its pixels from start to end, so `for pixel in edge`,
    `len(edge)` and `edge[0]` all work. The pixels at its vertices aren't part of it.

    Attributes:
        id (int): The edge's index, `edges(edge.id) is edge`
        start (Vertex): The vertex the pixels run away from
        end (Vertex): The vertex the pixels run towards
        pixels (list[Pixel]): The pixels along the edge, ordered start to end
        indices (np.ndarray): The LED indices of `pixels`, for numpy
        t (np.ndarray): How far along the edge each pixel is, from 0 at start to 1 at end, by distance
        length (float): The length of the wire from start, through every pixel, to end
    """

    __slots__ = ("id", "start", "end", "pixels", "indices", "t", "length",
                 "_pixels_rev", "_indices_rev", "_t_rev", "_at_start", "_at_end")

    def __init__(self, id: int, start: Vertex, end: Vertex, pixels: list[Pixel], positions: np.ndarray):
        self.id = id
        self.start = start
        self.end = end
        self.pixels = pixels
        self.indices = np.array([p.id for p in pixels], dtype=np.intp)

        # distance along the wire: start vertex -> each pixel -> end vertex
        points = np.vstack([start.position, positions[self.indices].astype(np.float64), end.position])
        along = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))])
        self.length = float(along[-1])
        if self.length > 0:
            self.t = along[1:-1] / self.length
        else:
            self.t = np.arange(1, len(pixels) + 1, dtype=np.float64) / (len(pixels) + 1)

        self._pixels_rev = pixels[::-1]
        self._indices_rev = self.indices[::-1].copy()
        self._t_rev = 1.0 - self.t[::-1]
        # filled in by Graph once every edge exists
        self._at_start: list[Edge] = []
        self._at_end: list[Edge] = []

    def __len__(self) -> int:
        return len(self.pixels)

    def __iter__(self):
        return iter(self.pixels)

    def __getitem__(self, i):
        return self.pixels[i]

    def __repr__(self) -> str:
        return f"Edge({self.id}, {self.start.id}->{self.end.id}, pixels={self.indices.tolist()})"

    @property
    def vertices(self) -> tuple[Vertex, Vertex]:
        """(start, end)"""
        return (self.start, self.end)

    def _is_start(self, v: Vertex) -> bool:
        if v is self.start:
            return True
        if v is self.end:
            return False
        raise ValueError(f"{v} is not an end of {self}")

    def other(self, v: Vertex) -> Vertex:
        """The vertex at the other end of the edge from v

        Example:
            ```
            next_vertex = edge.other(vertex)
            ```
        """
        return self.end if self._is_start(v) else self.start

    def pixels_from(self, v: Vertex) -> list[Pixel]:
        """The edge's pixels ordered going away from vertex v"""
        return self.pixels if self._is_start(v) else self._pixels_rev

    def indices_from(self, v: Vertex) -> np.ndarray:
        """The edge's LED indices ordered going away from vertex v"""
        return self.indices if self._is_start(v) else self._indices_rev

    def t_from(self, v: Vertex) -> np.ndarray:
        """How far along the edge each pixel of `pixels_from(v)` is, 0 at v and 1 at the other end"""
        return self.t if self._is_start(v) else self._t_rev

    def edges_at(self, v: Vertex) -> list["Edge"]:
        """The other edges meeting this one at vertex v, so the ways a chaser can carry on

        Example:
            ```
            options = edge.edges_at(edge.end)
            if options:
                edge = random.choice(options)
            ```
        """
        return self._at_start if self._is_start(v) else self._at_end

    def pixel_at(self, t: float, v: Optional[Vertex] = None) -> Optional[Pixel]:
        """The pixel nearest to the point t of the way along the edge, or None if the edge has no pixels

        Args:
            t (float): How far along, 0 to 1
            v (Optional[Vertex]): Measure t from this vertex. Defaults to the start
        """
        if not self.pixels:
            return None
        if v is not None and not self._is_start(v):
            t = 1.0 - t
        return self.pixels[int(np.argmin(np.abs(self.t - t)))]


E = TypeVar('E', bound='Graph')
class Graph(Fixture):
    """A fixture made of wires: edges of pixels joining vertices.

    Vertices are numbered by their position in `vertices`, edges by their position in `edges`.

    Args:
        positions: The position of every LED, in strip order
        vertices: For each vertex, its position and the LEDs sitting at it (may be empty)
        edges: For each edge, its start vertex, end vertex and the LEDs along it ordered start to end, not counting the LEDs at its vertices

    Every LED belongs to at most one edge or vertex.
    """

    def __init__(self,
                 positions: list[tuple[float, float, float]],
                 vertices: list[tuple[tuple[float, float, float], list[int]]],
                 edges: list[tuple[int, int, list[int]]]):
        super().__init__(positions)
        n = self._num_pixels

        self._pixel_vertex = np.full(n, -1, dtype=np.intp)
        """For each LED, the id of the vertex it's at, or -1"""
        self._pixel_edge = np.full(n, -1, dtype=np.intp)
        """For each LED, the id of the edge it's on, or -1"""

        def claim(i: int, what: str):
            if not 0 <= i < n:
                raise ValueError(f"{what} uses LED {i}, but there are only {n} LEDs")
            if self._pixel_vertex[i] != -1 or self._pixel_edge[i] != -1:
                raise ValueError(f"LED {i} is in {what} and also in another edge or vertex")

        self._vertices: list[Vertex] = []
        for vid, (pos, leds) in enumerate(vertices):
            for i in leds:
                claim(i, f"vertex {vid}")
                self._pixel_vertex[i] = vid
            self._vertices.append(Vertex(vid, pos, [self._pixels[i] for i in leds]))

        self._edges: list[Edge] = []
        for eid, (a, b, leds) in enumerate(edges):
            for v in (a, b):
                if not 0 <= v < len(self._vertices):
                    raise ValueError(f"edge {eid} uses vertex {v}, but there are only {len(self._vertices)} vertices")
            for i in leds:
                claim(i, f"edge {eid}")
                self._pixel_edge[i] = eid
            edge = Edge(eid, self._vertices[a], self._vertices[b], [self._pixels[i] for i in leds], self._positions)
            self._edges.append(edge)
            edge.start.edges.append(edge)
            if edge.end is not edge.start:
                edge.end.edges.append(edge)

        for edge in self._edges:
            edge._at_start = [e for e in edge.start.edges if e is not edge]
            edge._at_end = [e for e in edge.end.edges if e is not edge]

        self._neighbours = self._generate_neighbours()
        """For each LED, the LEDs next to it along the wires"""

    def _generate_neighbours(self) -> list[list[Pixel]]:
        # A chain per edge: start vertex, its pixels, end vertex. A vertex links to its own pixels.
        # A pixel's neighbours are the pixels it reaches without passing another pixel or a
        # vertex which has pixels (its own vertex excepted), so wires join through empty vertices.
        pix_adj: list[list[tuple[str, int]]] = [[] for _ in range(self._num_pixels)]
        vert_adj: list[list[tuple[str, int]]] = [[] for _ in self._vertices]

        def link(a: tuple[str, int], b: tuple[str, int]):
            (pix_adj if a[0] == "p" else vert_adj)[a[1]].append(b)
            (pix_adj if b[0] == "p" else vert_adj)[b[1]].append(a)

        for v in self._vertices:
            for i in v.indices:
                link(("v", v.id), ("p", int(i)))
        for e in self._edges:
            chain = [("v", e.start.id)] + [("p", int(i)) for i in e.indices] + [("v", e.end.id)]
            for a, b in zip(chain, chain[1:]):
                link(a, b)

        result: list[list[Pixel]] = []
        for i in range(self._num_pixels):
            own = int(self._pixel_vertex[i])
            found: list[int] = []
            seen = {("p", i)}
            stack = list(pix_adj[i])
            while stack:
                node = stack.pop()
                if node in seen:
                    continue
                seen.add(node)
                kind, k = node
                if kind == "p":
                    found.append(k)
                elif k == own or len(self._vertices[k].pixels) == 0:
                    stack.extend(vert_adj[k])
                else:
                    found.extend(int(j) for j in self._vertices[k].indices if j != i)
                    seen.update(("p", int(j)) for j in self._vertices[k].indices)
            result.append([self._pixels[j] for j in sorted(set(found))])
        return result

    @classmethod
    def from_txt(cls: type[E], path: str) -> E:
        """Load a graph from a graph text file"""
        from util import read_graph_txt
        return cls(*read_graph_txt(path))

    def edges(self, n: Optional[int] = None):
        """Same as the module level `edges()`, but for this graph rather than the active fixture"""
        return self._edges if n is None else self._edges[n]

    def vertices(self, n: Optional[int] = None):
        """Same as the module level `vertices()`, but for this graph rather than the active fixture"""
        return self._vertices if n is None else self._vertices[n]

    def edge_of(self, p: Union[Pixel, int]) -> Optional[Edge]:
        """Same as the module level `edge_of()`, but for this graph rather than the active fixture"""
        e = self._pixel_edge[p.id if isinstance(p, Pixel) else int(p)]
        return None if e < 0 else self._edges[e]

    def vertex_of(self, p: Union[Pixel, int]) -> Optional[Vertex]:
        """Same as the module level `vertex_of()`, but for this graph rather than the active fixture"""
        v = self._pixel_vertex[p.id if isinstance(p, Pixel) else int(p)]
        return None if v < 0 else self._vertices[v]

    def neighbours(self, p: Union[Pixel, int]) -> list[Pixel]:
        """Same as the module level `neighbours()`, but for this graph rather than the active fixture"""
        return self._neighbours[p.id if isinstance(p, Pixel) else int(p)]

class CompoundFixture(Fixture):
    def add(self, f: Fixture, name: str):
        ...


def _active_graph(name: str) -> Graph:
    fixture = get_active_fixture()
    if isinstance(fixture, Graph):
        return fixture
    if fixture is None:
        raise RuntimeError(f"{name}() only works while a fixture is drawing, use the Graph's own {name}() method outside draw()")
    raise TypeError(f"{name}() only works on a Graph fixture, but this pattern is drawing on a {type(fixture).__name__}")

@overload
def edges() -> list[Edge]: ...
@overload
def edges(n: int) -> Edge: ...

def edges(n: Optional[int] = None) -> Union[Edge, list[Edge]]:
    """The edges of the graph being drawn, like pixels() but for wires. Only works on a Graph fixture

    Args:
        n (Optional[int]): Grab only the nth edge

    Example:
        ```
        def draw():
            for edge in edges():
                for pixel, t in zip(edge.pixels, edge.t):
                    pixel.set(Color.mix(Color.red(), Color.blue(), t))
        ```
    """
    return _active_graph("edges").edges(n)

@overload
def vertices() -> list[Vertex]: ...
@overload
def vertices(n: int) -> Vertex: ...

def vertices(n: Optional[int] = None) -> Union[Vertex, list[Vertex]]:
    """The vertices of the graph being drawn, the points where edges meet. Only works on a Graph fixture

    Args:
        n (Optional[int]): Grab only the nth vertex

    Example:
        ```
        def draw():
            for vertex in vertices():
                if vertex.degree > 2:
                    for pixel in vertex.pixels:
                        pixel.set_white()
        ```
    """
    return _active_graph("vertices").vertices(n)

def edge_of(p: Union[Pixel, int]) -> Optional[Edge]:
    """The edge a pixel is on, or None if it's at a vertex or on no edge. Only works on a Graph fixture

    Args:
        p (Pixel | int): The pixel or its index
    """
    return _active_graph("edge_of").edge_of(p)

def vertex_of(p: Union[Pixel, int]) -> Optional[Vertex]:
    """The vertex a pixel sits at, or None if it isn't at one. Only works on a Graph fixture

    Args:
        p (Pixel | int): The pixel or its index
    """
    return _active_graph("vertex_of").vertex_of(p)

def neighbours(p: Union[Pixel, int]) -> list[Pixel]:
    """The pixels next to a pixel along the wires. Only works on a Graph fixture

    In the middle of an edge that's the pixels either side. Wires join up at vertices: a
    pixel at the end of an edge neighbours the pixels at its vertex, or if the vertex
    has none, the end pixels of the other edges there. Don't modify the list.

    Args:
        p (Pixel | int): The pixel or its index

    Example:
        ```
        # spread a glow along the wire
        for n in neighbours(spark):
            n.set_red()
        ```
    """
    return _active_graph("neighbours").neighbours(p)


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
    get_active_fixture()._lerp_target[n] = color.to_tuple()


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
    fixture = get_active_fixture()
    if fixture is None:
        print("No current fixture")
        return
    fixture._fps = fps


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
    get_active_fixture()._lerp_target[:] = color.to_tuple()


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
                f = frame() # 0, 1, 2
                print(f"{f} frames since the pattern started")
            ```
"""
    return _active_clock.frame if _active_clock is not None else 0

def seconds() -> int:
    """The number of seconds since the first draw() call

    This is presentation time, not the time the frame is computed
    """
    elapsed = _active_clock.elapsed() if _active_clock is not None else 0.0
    return math.floor(elapsed)

def millis() -> int:
    """The number of milliseconds since the first draw() call

    This is presentation time, not the time the frame is computed

        example:
            ```
            def draw():
                s = seconds()
                m = millis()
                print(f"{s}:{m} since the pattern started")
            ```
    """
    elapsed = _active_clock.elapsed() if _active_clock is not None else 0.0
    return math.floor(elapsed * 1000)


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
