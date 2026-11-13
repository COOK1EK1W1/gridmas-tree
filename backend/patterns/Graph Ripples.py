"""Rings of colour spread out from the junctions of the house, travelling along the
wires and round the corners, one pixel to the next.

Shows off: neighbours(), vertex.degree, vertex.pixels and edge.pixels_from().
"""

import random
from collections import deque

from gridmas import *
from house_fixtures import attach, fence_graph, front_graph

name = "Graph Ripples"
author = "Ciaran"

EVERY = 1.3
"""Seconds between ripples"""
SPEED = 35
"""Pixels per second along the wires"""
WIDTH = 3
"""Pixels wide"""
TAIL = 20
"""Frames for a ring to fade behind itself"""


def steps_from(vertex: Vertex) -> dict[int, int]:
    """How many pixels along the wires each pixel is from vertex"""
    first = list(vertex.pixels) or [e.pixels_from(vertex)[0] for e in vertex.edges if len(e)]
    steps = {p.id: 0 for p in first}
    todo = deque(first)
    while todo:
        p = todo.popleft()
        for q in neighbours(p):
            if q.id not in steps:
                steps[q.id] = steps[p.id] + 1
                todo.append(q)
    return steps


# each fixture runs its own ripples
_steps: dict[tuple[int, int], dict[int, int]] = {}
_ripples: dict[int, list[tuple[float, int, float]]] = {}
"""(when it started, which vertex, hue)"""


def draw_graph():
    key = id(get_active_fixture())
    ripples = _ripples.setdefault(key, [])
    now = millis() / 1000

    if not ripples or now - ripples[-1][0] >= EVERY:
        # junctions where three or more wires meet, or the ends of the wire if there aren't any
        junctions = [v for v in vertices() if v.degree >= 3] or [v for v in vertices() if v.degree == 1]
        ripples.append((now, random.choice(junctions).id, random.random()))

    fade(TAIL)
    kept = []
    for start, vertex_id, hue in ripples:
        if (key, vertex_id) not in _steps:
            _steps[(key, vertex_id)] = steps_from(vertices(vertex_id))
        steps = _steps[(key, vertex_id)]
        ring = (now - start) * SPEED
        if ring - WIDTH > max(steps.values(), default=0):
            continue  # it's run off every wire
        kept.append((start, vertex_id, hue))
        for i, n in steps.items():
            if ring - WIDTH <= n <= ring:
                pixels(i).set_hsl(hue, 1, 0.5)
    _ripples[key] = kept


attach()
fence_graph.set_draw_fn(draw_graph)
front_graph.set_draw_fn(draw_graph)


def display_update():
    pass
