"""Glowing snakes race round the wires of the house. At every corner each one picks a
way to go, sometimes splitting in two, and turns back at dead ends.

Shows off: edge.length, edge.pixel_at(), edge.other(), edge.edges_at() and vertex.pixels.
"""

import random

from gridmas import *
from house_fixtures import attach, fence_graph, front_graph

name = "Graph Chasers"
author = "Ciaran"

SPEED = (1.5, 3.0)
"""Metres of wire per second"""
TAIL = 25
"""Frames for a lit pixel to fade back to black"""
FEWEST = 3
MOST = 10
SPLIT = 0.3
"""Chance a chaser splits in two at a junction"""


class Chaser:
    def __init__(self, edge: Edge, start: Vertex, hue: float):
        self.edge = edge
        self.start = start
        """The vertex it's running away from"""
        self.s = 0.0
        """Metres along the edge from start"""
        self.speed = random.uniform(*SPEED)
        self.hue = hue


# each fixture runs its own chasers
_chasers: dict[int, list[Chaser]] = {}
_last: dict[int, float] = {}


def new_chaser() -> Chaser:
    edge = random.choice(edges())
    return Chaser(edge, random.choice(edge.vertices), random.random())


def draw_graph():
    key = id(get_active_fixture())
    chasers = _chasers.setdefault(key, [])
    now = millis() / 1000
    dt = min(now - _last.get(key, now), 0.1)
    _last[key] = now

    fade(TAIL)

    while len(chasers) < FEWEST:
        chasers.append(new_chaser())

    born = []
    for c in chasers:
        c.s += c.speed * dt
        # run on to the next edge each time this one ends
        while c.s >= c.edge.length:
            c.s -= c.edge.length
            at = c.edge.other(c.start)
            for pixel in at.pixels:
                pixel.set_hsl(c.hue, 1, 0.6)

            ways = c.edge.edges_at(at) or [c.edge]  # a dead end, turn back
            if len(ways) > 1 and random.random() < SPLIT and len(chasers) + len(born) < MOST:
                twin = Chaser(random.choice(ways), at, (c.hue + 0.15) % 1)
                ways = [w for w in ways if w is not twin.edge] or ways
                born.append(twin)
            c.edge, c.start = random.choice(ways), at

        head = c.edge.pixel_at(c.s / c.edge.length, c.start)
        if head is not None:
            head.set_hsl(c.hue, 1, 0.5)

    chasers.extend(born)
    # too many, the oldest ones go
    del chasers[:max(0, len(chasers) - MOST)]


attach()
fence_graph.set_draw_fn(draw_graph)
front_graph.set_draw_fn(draw_graph)


def display_update():
    pass
