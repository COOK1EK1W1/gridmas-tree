"""Holds a bunch of utility functions to make life easier
"""

import csv
import math
import numpy as np
from typing import Iterable, Union


def save_lights(light_locs: list[list[int]]) -> None:
    with open('tree.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(light_locs)

class tcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


PI = 3.1415926535897932384626433832795028841971693993

HALF_PI = PI/2

TWO_PI = PI*2

TAU = PI * 2


def clamp(val: Union[float, int], minv: Union[float, int], maxv: Union[float, int]):
    """Clamp a value between two values

        example:
            ```
            clamp(-1, 0, 1) # 0
            clamp(2, 0, 1) # 1
            clamp(0.5, 0, 1) # 0.5
            ```

    """
    return min(max(val, minv), maxv)

def read_tree_csv(location: str) -> tuple[list[tuple[float, float, float]], list[tuple[int, int]]]:
    points: list[tuple[float, float, float]] = []
    edges: list[tuple[int, int]] = []
    with open(location, newline="") as file:
        prev = (0, 0, 0)
        count = 0
        line_count = 0
        while line := file.readline():
            line_count += 1
            if not line.strip():
                continue
            if line[0] == "l":
                try:
                    count = int(line[1:])
                except:
                    raise Exception(f"Invalid number in line {line_count} in file {location}")
            else:
                parts = line.split(",")
                if 3 != len(parts):
                    raise Exception(f"Invalid coordinate in line {line_count} in file {location}")
                # an l line joins the previous vertex to this one, without one there's no edge
                if count and points:
                    edges.append((len(points) - 1, len(points) + count))
                # count pixels between the previous point and this one, then this point
                for i in range(count + 1):
                    norm = (i + 1) / (count + 1)
                    inorm = 1 - norm
                    try:
                        points.append((
                            prev[0] * inorm + float(parts[0]) * norm, 
                            prev[1] * inorm + float(parts[1]) * norm, 
                            prev[2] * inorm + float(parts[2]) * norm
                        ))
                    except:
                        raise Exception(f"Invalid number in line {line_count} in file {location}")
                count = 0
                prev = (float(parts[0]), float(parts[1]), float(parts[2]))
    return points, edges

Vec3 = tuple[float, float, float]


class GraphFormatError(ValueError):
    """A graph txt file could not be parsed, the message names the file and line"""


def _parse_coord(text: str, where: str) -> Vec3:
    parts = text.split(",")
    if len(parts) != 3:
        raise GraphFormatError(f"{where}: expected a coordinate 'x, y, z', got {text.strip()!r}")
    try:
        return (float(parts[0]), float(parts[1]), float(parts[2]))
    except ValueError:
        raise GraphFormatError(f"{where}: invalid number in coordinate {text.strip()!r}") from None


def read_graph_txt(location: str) -> tuple[list[Vec3], list[tuple[Vec3, list[int]]], list[tuple[int, int, list[int]]]]:
    """Read a graph fixture (wires with LEDs along them) from a txt file

    The file is read top to bottom and every LED line takes the next strip index, so the
    order of the lines is the order of the LEDs on the strip. `#` starts a comment, blank
    lines are ignored.

    ```
    v NAME x, y, z     declare a vertex (a corner / junction), no LED
    @ NAME             the next LED sits at vertex NAME
    @ NAME x, y, z     the same, but the LED's measured position is given
    e FROM TO N        the next N LEDs run along the wire FROM -> TO (N may be 0 or left out)
    x, y, z            the next LED, not on any vertex or edge (a plain csv line)
    ```

    Vertices must be declared before they are used, and can be shared by any number of
    edges and hold any number of LEDs (or none). An edge's LEDs are evenly spaced between
    its two ends, not on them. Each end is the vertex position, unless the LED right next
    to the run on the strip is an `@` LED of that vertex, then it is that LED's position,
    so `@ A` / `e A B 3` / `@ B` spaces the LEDs exactly like the strip does. The same pair
    of vertices may be joined by more than one edge, e.g. when the strip runs a corner to
    corner wire twice.

    example:
        ```
        v A 0, 0, 0
        v B 0, 0, 2
        v C -1.7, 0, 2
        @ A              # LED 0 on corner A
        e A B 25         # LEDs 1-25 up the wire
        @ B              # LED 26 on corner B
        e B C 21         # LEDs 27-47
        @ C -1.69, 0, 2  # LED 48, a touch short of C
        ```

    Returns:
        positions: one (x, y, z) per LED in strip order
        vertices: (position, LED indices at the vertex) per vertex, a vertex id is its index
        edges: (start vertex id, end vertex id, LED indices along the edge ordered start -> end)
    """
    # first pass: work out what every LED is, positions of edge LEDs need their neighbours
    # LED kinds: ("free", pos) / ("vertex", vid, pos) / ("edge", eid)
    leds: list[tuple] = []
    vertices: list[tuple[Vec3, list[int]]] = []
    names: dict[str, int] = {}
    edges: list[tuple[int, int, list[int]]] = []

    def vertex_id(name: str, where: str) -> int:
        if name not in names:
            raise GraphFormatError(f"{where}: unknown vertex {name!r}, declare it first with 'v {name} x, y, z'")
        return names[name]

    with open(location, newline="") as file:
        for line_no, raw in enumerate(file, 1):
            where = f"{location} line {line_no}"
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            kind, rest = (line.split(None, 1) + [""])[:2]
            if kind == "v":
                name, coord = (rest.split(None, 1) + [""])[:2]
                if not name or not coord.strip():
                    raise GraphFormatError(f"{where}: expected 'v NAME x, y, z'")
                if "," in name:
                    raise GraphFormatError(f"{where}: expected 'v NAME x, y, z', vertex names can't contain ','")
                if name in names:
                    raise GraphFormatError(f"{where}: vertex {name!r} is already declared")
                names[name] = len(vertices)
                vertices.append((_parse_coord(coord, where), []))
            elif kind == "@":
                name, coord = (rest.split(None, 1) + [""])[:2]
                if not name:
                    raise GraphFormatError(f"{where}: expected '@ NAME' or '@ NAME x, y, z'")
                vid = vertex_id(name, where)
                pos = _parse_coord(coord, where) if coord.strip() else vertices[vid][0]
                vertices[vid][1].append(len(leds))
                leds.append(("vertex", vid, pos))
            elif kind == "e":
                parts = rest.split()
                if len(parts) not in (2, 3):
                    raise GraphFormatError(f"{where}: expected 'e FROM TO N'")
                start, end = vertex_id(parts[0], where), vertex_id(parts[1], where)
                try:
                    count = int(parts[2]) if len(parts) == 3 else 0
                except ValueError:
                    raise GraphFormatError(f"{where}: invalid LED count {parts[2]!r}") from None
                if count < 0:
                    raise GraphFormatError(f"{where}: LED count can't be negative")
                eid = len(edges)
                edges.append((start, end, list(range(len(leds), len(leds) + count))))
                leds.extend(("edge", eid) for _ in range(count))
            elif kind[0] == "l" and kind[1:].isdigit():
                raise GraphFormatError(f"{where}: 'lN' lines are the old point cloud format, use 'e FROM TO N' between declared vertices")
            elif "," in line:
                leds.append(("free", _parse_coord(line, where)))
            else:
                raise GraphFormatError(f"{where}: unrecognised line {line!r}")

    # second pass: place the edge LEDs between their anchors
    positions: list[Vec3] = [led[-1] if led[0] != "edge" else (0.0, 0.0, 0.0) for led in leds]
    for start, end, idxs in edges:
        if not idxs:
            continue
        a, b = vertices[start][0], vertices[end][0]
        before, after = idxs[0] - 1, idxs[-1] + 1
        if before >= 0 and leds[before][0] == "vertex" and leds[before][1] == start:
            a = leds[before][2]
        if after < len(leds) and leds[after][0] == "vertex" and leds[after][1] == end:
            b = leds[after][2]
        n = len(idxs)
        for i, idx in enumerate(idxs):
            t = (i + 1) / (n + 1)
            positions[idx] = (a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t, a[2] * (1 - t) + b[2] * t)

    return positions, vertices, edges


def dist(a: Iterable[float], b: Iterable[float]) -> float:
    """The distance between two vectors

        example:
            ```
            dist([0, 0], [3, 4]) # 5
            ```
    """
    total = 0
    for pair in zip(a, b):
        total += (pair[0] - pair[1]) ** 2
    return math.sqrt(total)


def linear(x: float) -> float:
    """The linear activation function

    Activation function can be used with lerp to achieve different interpolations.

    The activations are taken from https://easings.net/# and are similar to the CSS implementations
    """
    return x


def step(x: float) -> float:
    """The step activation function"""
    x = np.asarray(x)
    return np.where(x > 0.5, 1, 0)


def ease_in_sine(x: float) -> float:
    """The ease in sine activation function"""
    x = np.asarray(x)
    return 1 - np.cos((x * np.pi) / 2)


def ease_out_sine(x: float) -> float:
    """The ease out sine activation function"""
    x = np.asarray(x)
    return np.sin((x * np.pi) / 2)


def ease_in_out_sine(x: float) -> float:
    """The ease in out sine activation function"""
    x = np.asarray(x)
    return -(np.cos(np.pi * x) - 1) / 2


def ease_in_cubic(x: float) -> float:
    """The ease in cubic activation function"""
    x = np.asarray(x)
    return x * x * x


def ease_out_cubic(x: float) -> float:
    """The ease out cubic activation function"""
    x = np.asarray(x)
    return 1 - np.power(1 - x, 3)


def ease_in_out_cubic(x: float) -> float:
    """The ease in out cubic activation function"""
    x = np.asarray(x)
    return np.where(x < 0.5, 4 * x * x * x, 1 - np.power(-2 * x + 2, 3) / 2)


def ease_in_quint(x: float) -> float:
    """The ease in quint activation function"""
    x = np.asarray(x)
    return x * x * x * x * x


def ease_out_quint(x: float) -> float:
    """The ease out quint activation function"""
    x = np.asarray(x)
    return 1 - np.power(1 - x, 5)


def ease_in_out_quint(x: float) -> float:
    """The ease in out quint activation function"""
    x = np.asarray(x)
    return np.where(x < 0.5, 16 * x * x * x * x * x, 1 - np.power(-2 * x + 2, 5) / 2)


def ease_in_circ(x: float) -> float:
    """The ease in circle activation function"""
    x = np.asarray(x)
    return 1 - np.sqrt(1 - np.power(x, 2))


def ease_out_circ(x: float) -> float:
    """The ease out circle activation function"""
    x = np.asarray(x)
    return np.sqrt(1 - np.power(x - 1, 2))


def ease_in_out_circ(x: float) -> float:
    """The ease in out circle activation function"""
    x = np.asarray(x)
    # clip before sqrt: np.where evaluates both branches eagerly (unlike
    # Python's if/else), so the untaken branch can otherwise go slightly
    # negative under sqrt right at the x=0/x=1 edges and warn/NaN even
    # though that value is discarded either way
    lower = (1 - np.sqrt(np.clip(1 - np.power(2 * x, 2), 0, None))) / 2
    upper = (np.sqrt(np.clip(1 - np.power(-2 * x + 2, 2), 0, None)) + 1) / 2
    return np.where(x < 0.5, lower, upper)


def ease_in_elastic(x: float) -> float:
    """The ease in elastic activation function"""
    x = np.asarray(x, dtype=np.float64)
    c4 = (2 * np.pi) / 3
    body = -np.power(2.0, 10 * x - 10) * np.sin((x * 10 - 10.75) * c4)
    return np.where(x <= 0, 0, np.where(x >= 1, 1, body))


def ease_out_elastic(x: float) -> float:
    """The ease out elastic activation function"""
    x = np.asarray(x, dtype=np.float64)
    c4 = (2 * np.pi) / 3
    body = np.power(2.0, -10 * x) * np.sin((x * 10 - 0.75) * c4) + 1
    return np.where(x <= 0, 0, np.where(x >= 1, 1, body))


def ease_in_out_elastic(x: float) -> float:
    """The ease in out elastic activation function"""
    x = np.asarray(x, dtype=np.float64)
    c5 = (2 * np.pi) / 4.5
    lower = -(np.power(2.0, 20 * x - 10) * np.sin((20 * x - 11.125) * c5)) / 2
    upper = (np.power(2.0, -20 * x + 10) * np.sin((20 * x - 11.125) * c5)) / 2 + 1
    body = np.where(x < 0.5, lower, upper)
    return np.where(x <= 0, 0, np.where(x >= 1, 1, body))


def ease_in_quad(x: float) -> float:
    """The ease in quad activation function"""
    x = np.asarray(x)
    return x * x


def ease_out_quad(x: float) -> float:
    """The ease out quad activation function"""
    x = np.asarray(x)
    return 1 - (1 - x) * (1 - x)


def ease_in_out_quad(x: float) -> float:
    """The ease in out quad activation function"""
    x = np.asarray(x)
    return np.where(x < 0.5, 2 * x * x, 1 - np.power(-2 * x + 2, 2) / 2)


def ease_in_quart(x: float) -> float:
    """The ease in quart activation function"""
    x = np.asarray(x)
    return x * x * x * x


def ease_out_quart(x: float) -> float:
    """The ease out quart activation function"""
    x = np.asarray(x)
    return 1 - np.power(1 - x, 4)


def ease_in_out_quart(x: float) -> float:
    """The ease in out quart activation function"""
    x = np.asarray(x)
    return np.where(x < 0.5, 8 * x * x * x * x, 1 - np.power(-2 * x + 2, 4) / 2)


def ease_in_expo(x: float) -> float:
    """The ease in expo activation function"""
    x = np.asarray(x, dtype=np.float64)
    return np.where(x <= 0, 0, np.power(2.0, 10 * x - 10))


def ease_out_expo(x: float) -> float:
    """The ease out expo activation function"""
    x = np.asarray(x, dtype=np.float64)
    return np.where(x >= 1, 1, 1 - np.power(2.0, -10 * x))


def ease_in_out_expo(x: float) -> float:
    """The ease in out expo activation function"""
    x = np.asarray(x, dtype=np.float64)
    body = np.where(x < 0.5, np.power(2.0, 20 * x - 10) / 2, (2 - np.power(2.0, -20 * x + 10)) / 2)
    return np.where(x <= 0, 0, np.where(x >= 1, 1, body))


def ease_in_back(x: float) -> float:
    """The ease in back activation function"""
    x = np.asarray(x)
    c1 = 1.70158
    c3 = c1 + 1
    return c3 * x * x * x - c1 * x * x


def ease_out_back(x: float) -> float:
    """The ease out back activation function"""
    x = np.asarray(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * np.power(x - 1, 3) + c1 * np.power(x - 1, 2)


def ease_in_out_back(x: float) -> float:
    """The ease in out back activation function"""
    x = np.asarray(x)
    c1 = 1.70158
    c2 = c1 * 1.525
    return np.where(
        x < 0.5,
        (np.power(2 * x, 2) * ((c2 + 1) * 2 * x - c2)) / 2,
        (np.power(2 * x - 2, 2) * ((c2 + 1) * (x * 2 - 2) + c2) + 2) / 2,
    )


def ease_in_bounce(x: float) -> float:
    """The ease in bounce activation function"""
    return 1 - ease_out_bounce(1 - np.asarray(x))


def ease_out_bounce(x: float) -> float:
    """The ease out bounce activation function"""
    x = np.asarray(x, dtype=np.float64)
    n1 = 7.5625
    d1 = 2.75

    xa = x
    ra = n1 * xa * xa

    xb = x - 1.5
    rb = n1 * (xb / d1) * xb + 0.75

    xc = x - 2.25
    rc = n1 * (xc / d1) * xc + 0.9375

    xd = x - 2.625
    rd = n1 * (xd / d1) * xd + 0.984375

    return np.select(
        [x < 1 / d1, x < 2 / d1, x < 2.5 / d1],
        [ra, rb, rc],
        default=rd,
    )


def ease_in_out_bounce(x: float) -> float:
    """The ease in out bounce activation function"""
    x = np.asarray(x)
    return np.where(
        x < 0.5,
        (1 - ease_out_bounce(1 - 2 * x)) / 2,
        (1 + ease_out_bounce(2 * x - 1)) / 2,
    )
