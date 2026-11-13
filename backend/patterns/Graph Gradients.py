"""Every corner of the house has its own slowly drifting colour, and every wire blends
smoothly from the colour at one end to the colour at the other.

Shows off: vertices(), edges(), edge.start / edge.end, edge.t and vertex.pixels.
"""

import random

from gridmas import *
from house_fixtures import attach, fence_graph, front_graph

name = "Graph Gradients"
author = "Ciaran"

DRIFT = 0.05
"""How fast the corners change colour, hue turns per second"""

# every corner starts on its own hue and drifts at its own speed
_hues: dict[tuple[int, int], tuple[float, float]] = {}


def hue(vertex: Vertex) -> float:
    key = (id(get_active_fixture()), vertex.id)
    if key not in _hues:
        _hues[key] = (random.random(), DRIFT * random.uniform(0.5, 1.5) * random.choice((-1, 1)))
    start, speed = _hues[key]
    return (start + speed * millis() / 1000) % 1


def draw_graph():
    colours = {vertex.id: Color.hsl(hue(vertex), 1, 0.5) for vertex in vertices()}

    for edge in edges():
        a, b = colours[edge.start.id], colours[edge.end.id]
        # edge.t is how far along the wire each pixel is, 0 at the start, 1 at the end
        for pixel, t in zip(edge.pixels, edge.t):
            pixel.set(Color.mix(a, b, t))

    for vertex in vertices():
        for pixel in vertex.pixels:
            pixel.set(colours[vertex.id])


attach()
fence_graph.set_draw_fn(draw_graph)
front_graph.set_draw_fn(draw_graph)


def display_update():
    pass
