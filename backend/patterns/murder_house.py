"""Murder! For guests arriving at a murder mystery.

The hedge loops: MURDUR slashed on in blood one huge letter at a time, an arrow pointing
right, then MURDUR scrolling along the hedge and the arrow again. Meanwhile blood runs
out from the front door through every wire of the house and along the fence, a fresh
gush running out every so often, and drops of blood form at the corners high on the
front of the house and run down its wires, splashing where they land.
"""

import heapq
import math
from typing import Optional

import numpy as np

from fixture import Edge, Fixture, Graph, Vertex, get_active_fixture
from house_fixtures import attach, fence_graph, front_graph, hedge_wall
from gridmas import *

name = "Murder!"
author = "Ciaran"

GAMMA = 1.8

BLOOD = np.array([1.0, 0.0, 0.0])
FRESH = np.array([1.0, 0.18, 0.12])
"""Blood that's just been spilt, a touch brighter"""

WORD = "MURDUR"


## the hedge's loop, in seconds

LETTER_TIME = 0.8
"""Each letter on its own for this long, slashed on in the first WRITE_TIME of it"""
WRITE_TIME = 0.45
ARROW_TIME = 2.5
SCROLL_SPEED = 1.6
"""In hedge units per second, the hedge is 2 wide"""
SCROLL_GAP = 0.3
"""Between letters while scrolling"""


def smoothstep(e0: float, e1: float, x):
    x = np.clip((np.asarray(x, dtype=float) - e0) / (e1 - e0), 0, 1)
    return x * x * (3 - 2 * x)


def now() -> float:
    return millis() / 1000


def show(v: np.ndarray):
    """Put 0-1 floats on the active fixture"""
    f = get_active_fixture()
    f._rgb[:] = (255 * np.clip(v, 0, 1) ** GAMMA).astype(np.uint8)
    f._changed_arr[:] = True


## the wires: blood runs out along them

FILL_TIME = 3.0
"""Seconds for the first blood to reach the end of every wire"""
GUSH_EVERY = 6.0

DRIPS_PER_SECOND = 6.0
DRIP_COLOR = np.array([0.8, 0.05, 0.03])
"""Brighter than the blood lying on the wires, but not glaring"""
DRIP_GRAVITY = 2.0
"""Metres per second per second, slower than real so you can watch them fall"""
DRIP_MAX_SPEED = 1.8
DRIP_TRAIL = 0.45
"""Metres of wet trail behind a falling drop"""
DRIP_BEAD = (0.3, 1.0)
"""Seconds a drop swells at the top before it lets go"""
SPLASH = 0.25
"""How far along the wires a drop splashes when it lands"""


def falls(edge: Edge, top: Vertex) -> bool:
    """Whether a drop at top would fall down this edge: it has to go mostly downwards"""
    d = edge.other(top).position - top.position
    return d[2] < 0 and -d[2] > 0.7 * float(np.linalg.norm(d))


class Drop:
    __slots__ = ("edge", "top", "s", "v", "bead", "bead_for")

    def __init__(self, edge: Edge, top: Vertex, bead: float):
        self.edge = edge
        self.top = top
        """The vertex it's falling away from"""
        self.s = 0.0
        """Metres down the edge"""
        self.v = 0.0
        self.bead = bead
        self.bead_for = bead


class Drips:
    """Drops of blood forming at the corners high on the wires and running down them"""

    def __init__(self, graph: Graph):
        self.n = graph._num_pixels
        self.down = {v.id: [e for e in v.edges if falls(e, v)] for v in graph.vertices()}
        self.sources = [v for v in graph.vertices() if self.down[v.id] and v.z > 0.5]
        weights = np.array([v.z for v in self.sources])
        self.weights = weights / weights.sum()
        self.drops: list[Drop] = []
        self.splashes: list[tuple[np.ndarray, np.ndarray, float]] = []
        """(pixels, how hard each is splashed, when)"""
        self.rng = np.random.default_rng()
        self.last: Optional[float] = None

    def splash(self, at: Vertex, t: float):
        idx, hit = [at.indices], [np.ones(len(at.indices))]
        for edge in at.edges:
            along = edge.t_from(at) * edge.length
            near = along < SPLASH
            idx.append(edge.indices_from(at)[near])
            hit.append(1 - along[near] / SPLASH)
        self.splashes.append((np.concatenate(idx), np.concatenate(hit), t))

    def step(self, t: float):
        dt = 0.0 if self.last is None else min(max(t - self.last, 0.0), 0.1)
        self.last = t

        for _ in range(self.rng.poisson(DRIPS_PER_SECOND * dt) if self.sources else 0):
            top = self.sources[self.rng.choice(len(self.sources), p=self.weights)]
            edge = self.down[top.id][self.rng.integers(len(self.down[top.id]))]
            self.drops.append(Drop(edge, top, self.rng.uniform(*DRIP_BEAD)))

        alive = []
        for d in self.drops:
            if d.bead > 0:
                d.bead -= dt
                alive.append(d)
                continue
            dz = d.top.z - d.edge.other(d.top).z
            d.v = min(DRIP_MAX_SPEED, d.v + DRIP_GRAVITY * dt * dz / max(d.edge.length, 1e-9))
            d.s += d.v * dt
            landed = False
            while d.s >= d.edge.length:
                bottom = d.edge.other(d.top)
                ways = self.down[bottom.id]
                if not ways:
                    self.splash(bottom, t)
                    landed = True
                    break
                d.s -= d.edge.length
                d.top = bottom
                d.edge = ways[self.rng.integers(len(ways))]
            if not landed:
                alive.append(d)
        self.drops = alive
        self.splashes = [s for s in self.splashes if t - s[2] < 1.5]

    def light(self, t: float) -> np.ndarray:
        """How lit each pixel is by drops (0-1)"""
        lit = np.zeros(self.n)
        for d in self.drops:
            idx = d.edge.indices_from(d.top)
            along = d.edge.t_from(d.top) * d.edge.length
            if d.bead > 0:
                # swelling at the top
                grow = 1 - d.bead / d.bead_for
                lit[d.top.indices] = np.maximum(lit[d.top.indices], 0.3 + 0.7 * grow)
                near = along < 0.05 * grow + 0.01
                lit[idx[near]] = np.maximum(lit[idx[near]], 0.6 * grow)
                continue
            head = np.exp(-((along - d.s) / 0.04) ** 2)
            behind = d.s - along
            trail = np.where((behind > 0) & (behind < DRIP_TRAIL), 0.7 * (1 - behind / DRIP_TRAIL) ** 2, 0)
            lit[idx] = np.maximum(lit[idx], np.maximum(head, trail))
            if d.s < DRIP_TRAIL:
                lit[d.top.indices] = np.maximum(lit[d.top.indices], 0.7 * (1 - d.s / DRIP_TRAIL) ** 2)
        for idx, hit, when in self.splashes:
            lit[idx] = np.maximum(lit[idx], hit * math.exp(-(t - when) / 0.35))
        return lit


class Wires:
    def __init__(self, graph: Graph, source: int, drips: bool = False, level: float = 1.0):
        self.drips = Drips(graph) if drips else None
        self.level = level
        """How bright the blood lying on the wires is, lower to make the drips stand out"""
        P = graph._positions.astype(float)
        self.z = P[:, 2]
        self.n = len(P)

        # distance along the wires from the source vertex, so blood follows them round corners
        dist = np.full(self.n, np.inf)
        todo = [(0.0, int(i)) for i in graph.vertices(source).indices]
        heapq.heapify(todo)
        while todo:
            d, i = heapq.heappop(todo)
            if d >= dist[i]:
                continue
            dist[i] = d
            for p in graph.neighbours(i):
                nd = d + float(np.linalg.norm(P[p.id] - P[i]))
                if nd < dist[p.id]:
                    heapq.heappush(todo, (nd, p.id))
        if np.isfinite(dist).any():
            dist[~np.isfinite(dist)] = dist[np.isfinite(dist)].max()
        else:
            dist[:] = 0
        self.dist = dist
        self.speed = max(float(dist.max()), 0.1) / FILL_TIME
        """Metres of wire per second"""

        # how upright each pixel's wire is: blood drips down the uprights
        self.upright = np.zeros(self.n)
        for edge in graph.edges():
            d = edge.end.position - edge.start.position
            self.upright[edge.indices] = abs(d[2]) / max(float(np.linalg.norm(d)), 1e-9)

        self.wobble = np.random.default_rng(7).uniform(0, 1, self.n)

    def draw(self):
        t = now()
        ahead = t * self.speed - self.dist
        wet = smoothstep(0, 0.05, ahead)

        # running down the uprights, lying still along the rest
        drip = 0.62 + 0.38 * np.sin(self.z * 22 + t * 9 + self.wobble * 2)
        body = 0.7 * (1 - self.upright) + 0.85 * self.upright * drip

        # the leading edge of the first blood, then a fresh gush out from the door every so often
        gush = (t % GUSH_EVERY) * self.speed - self.dist
        fresh = np.exp(-np.maximum(ahead, 0) / 0.25) * wet
        fresh = np.maximum(fresh, np.exp(-np.abs(gush) / 0.3) * (t > GUSH_EVERY))

        v = BLOOD * (wet * body * self.level)[:, None] + (FRESH - BLOOD * 0.3) * (fresh * self.level)[:, None]

        if self.drips is not None:
            if t > FILL_TIME:
                self.drips.step(t)
            drop = self.drips.light(t)[:, None]
            v = v * (1 - drop) + DRIP_COLOR * drop

        show(v)


## the hedge: drawn in blood

LETTERS: dict[str, list[list[tuple[float, float]]]] = {
    # strokes in a 1 wide, 1 tall box, y up, in the order they're written
    "M": [[(0, 0), (0, 1), (0.5, 0.42), (1, 1), (1, 0)]],
    "U": [[(0, 1), (0, 0.32), (0.08, 0.1), (0.25, 0), (0.75, 0), (0.92, 0.1), (1, 0.32), (1, 1)]],
    "R": [[(0, 0), (0, 1), (0.65, 1), (0.92, 0.9), (1, 0.75), (0.92, 0.6), (0.65, 0.5), (0, 0.5)],
          [(0.45, 0.5), (1, 0)]],
    "D": [[(0, 0), (0, 1), (0.55, 1), (0.85, 0.85), (1, 0.6), (1, 0.4), (0.85, 0.15), (0.55, 0), (0, 0)]],
    "E": [[(1, 1), (0, 1), (0, 0), (1, 0)], [(0, 0.5), (0.75, 0.5)]],
    "→": [[(0, 0.5), (1, 0.5)], [(0.55, 0.95), (1, 0.5), (0.55, 0.05)]],
}

HEDGE_ASPECT = 16 / 9
"""The hedge's points are squashed onto x -1 to 1, z 0 to height(), the real hedge is 16:9"""
TALL = 2 / HEDGE_ASPECT
"""Everything on the hedge is measured in its true proportions: 2 wide, TALL tall"""
LETTER_HEIGHT = 0.95
LETTER_WIDTH = 0.85
ARROW_WIDTH = 1.5
ARROW_HEIGHT = 0.8
STROKE = 0.08
"""Half the width of a stroke. The hedge's pixels are ~0.04 apart, so a stroke is about two pixels wide"""
SOFT = 0.006
"""A hard edge, a soft one smears the letters"""


class Strokes:
    """Some strokes on the hedge, which can be written a bit at a time and slid sideways"""

    def __init__(self, xz: np.ndarray, glyphs: list[tuple[str, float, float, float, float]]):
        """glyphs: (character, left, bottom, width, height)"""
        a, b, start = [], [], []
        done = 0.0
        for ch, x0, z0, w, h in glyphs:
            for stroke in LETTERS[ch]:
                pts = [(x0 + x * w, z0 + y * h) for x, y in stroke]
                for p, q in zip(pts, pts[1:]):
                    a.append(p)
                    b.append(q)
                    start.append(done)
                    done += math.dist(p, q)
        self.a, self.b = np.array(a), np.array(b)
        self.seg_len = np.linalg.norm(self.b - self.a, axis=1)
        self.start = np.array(start)
        self.length = done
        self.xz = xz
        self.right = float(max(self.a[:, 0].max(), self.b[:, 0].max()))
        self.left = float(min(self.a[:, 0].min(), self.b[:, 0].min()))

    def ink(self, written: float = 1.0, dx: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
        """How inked each pixel is (0-1) with this much written and slid dx right, and the tip of the pen"""
        n = len(self.xz)
        f = np.clip((written * self.length - self.start) / np.maximum(self.seg_len, 1e-9), 0, 1)
        # only the strokes that are written and near the hedge
        lo = np.minimum(self.a[:, 0], self.b[:, 0]) + dx
        hi = np.maximum(self.a[:, 0], self.b[:, 0]) + dx
        drawn = (f > 0) & (hi > -1 - STROKE * 2) & (lo < 1 + STROKE * 2)
        if not drawn.any():
            return np.zeros(n), np.zeros(n)
        shift = np.array([dx, 0.0])
        end = self.a + (self.b - self.a) * f[:, None] + shift
        a = self.a[drawn] + shift
        ab = end[drawn] - a
        rel = self.xz[:, None, :] - a[None]
        u = np.clip((rel * ab[None]).sum(2) / np.maximum((ab * ab).sum(1), 1e-12)[None], 0, 1)
        d = np.linalg.norm(rel - u[..., None] * ab[None], axis=2).min(axis=1)
        ink = 1 - smoothstep(STROKE, STROKE + SOFT, d)

        fresh = np.zeros(n)
        writing = drawn & (f < 1)
        if writing.any():
            tip = np.linalg.norm(self.xz[:, None] - end[writing][None], axis=2).min(axis=1)
            fresh = 1 - smoothstep(0.04, 0.14, tip)
        return ink, fresh


class Hedge:
    def __init__(self, wall: Fixture):
        P = wall._positions.astype(float)
        xz = np.stack([P[:, 0], P[:, 2] / max(float(P[:, 2].max()), 1e-9) * TALL], axis=1)
        self.n = len(P)

        middle = (TALL - LETTER_HEIGHT) / 2
        self.letters = [Strokes(xz, [(ch, -LETTER_WIDTH / 2, middle, LETTER_WIDTH, LETTER_HEIGHT)]) for ch in WORD]
        self.arrow = Strokes(xz, [("→", -ARROW_WIDTH / 2, (TALL - ARROW_HEIGHT) / 2, ARROW_WIDTH, ARROW_HEIGHT)])
        self.word = Strokes(xz, [(ch, k * (LETTER_WIDTH + SCROLL_GAP), middle, LETTER_WIDTH, LETTER_HEIGHT)
                                 for k, ch in enumerate(WORD)])

        # the word comes on from the right and goes off the left
        self.scroll_from = 1 + STROKE * 2 - self.word.left
        self.scroll_to = -1 - STROKE * 2 - self.word.right
        scroll_time = (self.scroll_from - self.scroll_to) / SCROLL_SPEED
        self.parts = [("spell", LETTER_TIME * len(WORD)), ("arrow", ARROW_TIME),
                      ("scroll", scroll_time), ("arrow", ARROW_TIME)]
        self.loop = sum(length for _, length in self.parts)

    def ink(self, t: float) -> tuple[np.ndarray, np.ndarray]:
        s = t % self.loop
        for part, length in self.parts:
            if s < length:
                break
            s -= length

        if part == "spell":
            k = min(int(s // LETTER_TIME), len(WORD) - 1)
            return self.letters[k].ink((s - k * LETTER_TIME) / WRITE_TIME)
        if part == "arrow":
            # slashed on, then nudging to the right
            nudge = 0.12 * abs(math.sin(max(0.0, s - 0.4) * math.pi * 1.6))
            return self.arrow.ink(s / 0.4, nudge)
        return self.word.ink(1.0, self.scroll_from - s * SCROLL_SPEED)

    def draw(self):
        ink, fresh = self.ink(now())
        show(BLOOD * ink[:, None] + (FRESH - BLOOD) * (fresh * ink)[:, None])


FENCE = Wires(fence_graph, source=0)
FRONT = Wires(front_graph, source=0, drips=True, level=0.3)
"""Vertex 0 is the bottom corner of the front door"""
HEDGE = Hedge(hedge_wall)

attach()


def display_update():
    for fixture, draw in ((fence_graph, FENCE.draw), (front_graph, FRONT.draw), (hedge_wall, HEDGE.draw)):
        fixture.set_draw_fn(draw)
