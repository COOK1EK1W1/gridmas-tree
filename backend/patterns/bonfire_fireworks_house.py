"""Bonfire night fireworks on the house: the hedge, the fence and the front.

An endless show with no fixed running order. A director keeps two tracks going, one for
the hedge and the front of the house and one for the fence, and whenever a track's
segment finishes it picks another at random (never one it has just done). Segments are
small scripts, a sweep of shells across the hedge, rockets from the corners of the
house, a rainbow, a barrage... and are written as generators that yield how many seconds
to wait, so new ones are easy to add to SEGMENTS / FENCE_SEGMENTS.

The hedge is a 2D sky. Particles fly freely under gravity and drag and are splatted
into a grid that gets blurred and sampled at each pixel.

The front of the house and the fence are wires. Their pixels are graphs, so sparks
there travel *along the edges* with a velocity: drag slows them, gravity pulls them down
vertical edges and slows them going up, and at junctions they pick a way or split.
  - On the front, rockets go up the walls from the bottom corners of the door and window
    until they run out of upward wire, then burst. The burst is a shell expanding through
    space: everywhere the shell crosses the house's other lines it lights them and sets
    sparks running along them, so a burst over the door spreads into the windows.
  - On the fence, fireworks run horizontally: rockets are fired from either end and burst
    somewhere near or past the middle into fire coloured sparks that fly out fast both
    ways, slow and fade. Fire sprinklers spray flames along it.
"""

import math
from typing import Callable, Iterator, Optional

import numpy as np

from pixel_driver import DISPLAY_TICK_FPS
from fixture import Fixture, get_active_fixture
from house_fixtures import attach, fence_graph, front_graph, hedge_wall
from gridmas import *

name = "Bonfire Night Fireworks (House)"
author = "Ciaran"

FPS = 45
DT = 1 / FPS

attach(FPS)

RNG = np.random.default_rng()

## tuning

BRIGHTNESS = 1.0
"""Overall output level, turn down if the house is too bright"""
REST_LEVEL = 0.5
"""Bursts go up to full brightness, everything else (trails, embers, fountains, glows) is kept under this"""
GAMMA = 2.0
"""LEDs are linear, eyes aren't: this makes fades look like fades"""
GRAVITY = 0.9
"""Hedge, in hedge heights per second per second"""
WIRE_GRAVITY = 4.0
"""Front and fence, in metres per second per second"""
TRAIL_DECAY = 0.78
"""How much of last frame's light each hedge pixel keeps, the motion blur behind every spark"""
WIRE_TRAIL_DECAY = 0.84
MAX_PARTICLES = 5000
MAX_WIRE_PARTICLES = 1500

## colours

COLOURS = {
    "red":    (1.00, 0.04, 0.02),
    "green":  (0.05, 1.00, 0.08),
    "blue":   (0.08, 0.22, 1.00),
    "purple": (0.60, 0.08, 1.00),
    "gold":   (1.00, 0.52, 0.08),
    "silver": (0.85, 0.85, 1.00),
    "orange": (1.00, 0.28, 0.00),
    "cyan":   (0.00, 0.80, 1.00),
    "pink":   (1.00, 0.15, 0.45),
}
BRIGHT_COLOURS = ["red", "orange", "pink", "purple", "blue", "cyan", "green"]
"""In rainbow order"""
GOLD = np.array(COLOURS["gold"])
EMBER = np.array((1.0, 0.30, 0.04))
WHITE = np.ones(3)
GOLD_KINDS = ("willow", "kamuro", "crackle")
FIRE_COLOURS = {
    "flame":  (1.00, 0.45, 0.02),
    "gold":   (1.00, 0.60, 0.10),
    "red":    (1.00, 0.08, 0.00),
    "amber":  (1.00, 0.30, 0.00),
    "yellow": (1.00, 0.80, 0.25),
}
FIRE_STOPS = np.array([0.0, 0.2, 0.55, 1.0])
FIRE_RAMP = np.array([(1.0, 0.85, 0.45), (1.0, 0.50, 0.06), (0.95, 0.15, 0.0), (0.45, 0.02, 0.0)])
"""What a flame looks like as it burns out: yellow-white, orange, red, dull red"""


def fire_ramp(t: np.ndarray) -> np.ndarray:
    return np.stack([np.interp(t, FIRE_STOPS, FIRE_RAMP[:, c]) for c in range(3)], axis=1)


def fire_colour() -> np.ndarray:
    return np.array(FIRE_COLOURS[str(RNG.choice(list(FIRE_COLOURS)))], dtype=float)


def bright_colour() -> np.ndarray:
    return colour(str(RNG.choice(BRIGHT_COLOURS)))


def colour(name: str) -> np.ndarray:
    return np.array(COLOURS[name], dtype=float)


def random_colour() -> np.ndarray:
    if RNG.random() < 0.2:
        return colour(str(RNG.choice(["gold", "silver"])))
    return colour(str(RNG.choice(BRIGHT_COLOURS)))


def main_colour(shell: dict) -> np.ndarray:
    return GOLD if shell["kind"] in GOLD_KINDS else shell["c1"]


## directions sparks leave a hedge shell in

def sphere(n: int) -> np.ndarray:
    """A shell is a sphere seen side on, so it's denser in the middle"""
    d = RNG.normal(size=(n, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    return d[:, [0, 2]]


def ring(n: int) -> np.ndarray:
    """A ring tilted a random amount towards or away from you, so an ellipse"""
    a = np.linspace(0, 2 * math.pi, n, endpoint=False) + RNG.uniform(0, 2 * math.pi)
    squash = RNG.uniform(0.25, 1.0)
    turn = RNG.uniform(0, math.pi)
    x, y = np.cos(a), np.sin(a) * squash
    c, s = math.cos(turn), math.sin(turn)
    return np.stack([x * c - y * s, x * s + y * c], axis=1)


## particles

FIELDS = {
    "pos": 2, "vel": 2, "rgb": 3,
    "age": 0, "life": 0, "drag": 0, "grav": 0, "bright": 0,
    "hot": 0,      # seconds spent white hot after being born
    "emit": 0,     # embers shed per second
    "flick": 0,    # 0 steady, 1 sparkle, 2 strobe, 3 crackle
    "split_t": 0,  # age it breaks apart at
    "split_k": 0,  # what it breaks into
    "phase": 0,
    "edge": 0,     # wires only: the edge it's on, pos is how far along it and vel its speed
    "branch": 0,   # wires only: how many more junctions it can split at
    "boom": 0,     # 1 for stars from a burst, which can go to full brightness
    "fire": 0,     # 1 to colour it like a flame burning out instead of rgb
}
STEADY, SPARKLE, STROBE, CRACKLE = 0, 1, 2, 3
SPLIT_NONE, SPLIT_CROSSETTE, SPLIT_CRACKLE, SPLIT_PEONY = 0, 1, 2, 3
DEFAULTS = {"age": 0, "drag": 2.0, "grav": 1.0, "bright": 1.0, "hot": 0.0, "emit": 0.0,
            "flick": STEADY, "split_t": np.inf, "split_k": SPLIT_NONE, "edge": 0, "branch": 0, "boom": 0, "fire": 0}


class Particles:
    """A structure of numpy arrays, one row per spark"""

    def __init__(self, dims: int):
        self.dims = dims
        self.a = {k: np.zeros((0, self._width(k)) if self._width(k) else (0,)) for k in FIELDS}
        self.pending: list[dict[str, np.ndarray]] = []

    def _width(self, k: str) -> int:
        return self.dims if k in ("pos", "vel") else FIELDS[k]

    def __len__(self):
        return len(self.a["age"])

    def spawn(self, n: int, **kw):
        if n <= 0:
            return
        batch = {}
        for k in FIELDS:
            w = self._width(k)
            if k in kw:
                v = kw[k]
            elif k == "phase":
                v = RNG.random(n)
            else:
                v = DEFAULTS[k]
            shape = (n, w) if w else (n,)
            batch[k] = np.array(np.broadcast_to(np.asarray(v, dtype=float), shape))
        self.pending.append(batch)

    def clone(self, i: int, **over):
        row = {k: v[i] for k, v in self.a.items()}
        row.update(over)
        self.spawn(1, **row)

    def flush(self):
        if self.pending:
            self.a = {k: np.concatenate([self.a[k]] + [b[k] for b in self.pending]) for k in FIELDS}
            self.pending = []

    def keep(self, mask: np.ndarray):
        self.a = {k: v[mask] for k, v in self.a.items()}

    def light(self) -> tuple[np.ndarray, np.ndarray]:
        """The colour and brightness every spark shows this frame"""
        a = self.a
        n = len(self)
        t = np.clip(a["age"] / a["life"], 0, 1)
        level = (1 - t) ** 1.6 * a["bright"]

        flick = a["flick"]
        level = np.where(flick == SPARKLE, level * RNG.uniform(0.45, 1.0, n), level)
        strobe = np.sin(2 * math.pi * (9 * a["age"] + a["phase"])) > 0.2
        level = np.where(flick == STROBE, level * strobe * 1.4, level)
        pop = RNG.random(n) < 0.22
        level = np.where(flick == CRACKLE, pop * 1.6 * (1 - t) ** 0.5 * a["bright"], level)

        # white hot when born, the colour, then a little ember red as it dies
        whiten = np.clip(1 - a["age"] / np.maximum(a["hot"], 1e-6), 0, 1) * (a["hot"] > 0)
        whiten = np.maximum(whiten, (flick == CRACKLE) * 0.85)
        cool = np.clip((t - 0.7) / 0.3, 0, 1) * 0.5
        rgb = a["rgb"] * (1 - cool[:, None]) + EMBER * cool[:, None]
        rgb = rgb * (1 - whiten[:, None]) + WHITE * whiten[:, None]
        fire = a["fire"] > 0
        if np.any(fire):
            rgb[fire] = fire_ramp(t[fire])
        return rgb, level


def resolve(spec: dict, n: int) -> dict:
    """(lo, hi) in a spark recipe means pick uniformly per spark"""
    return {k: RNG.uniform(v[0], v[1], n) if isinstance(v, tuple) else v for k, v in spec.items()}


def blur(g: np.ndarray, axis: int) -> np.ndarray:
    """[1 4 6 4 1] along one axis"""
    k = (1 / 16, 4 / 16, 6 / 16, 4 / 16, 1 / 16)
    n = g.shape[axis]
    pad = [(0, 0)] * g.ndim
    pad[axis] = (2, 2)
    p = np.pad(g, pad)
    return sum(w * np.take(p, range(i, i + n), axis=axis) for i, w in enumerate(k))


def splat(shape: tuple[int, ...], cells: np.ndarray, rgb: np.ndarray) -> np.ndarray:
    """Add colours into a grid at fractional cell positions, shared between the nearest cells"""
    dims = len(shape)
    size = int(np.prod(shape))
    base = np.floor(cells).astype(int)
    frac = cells - base
    ok = np.all((base >= 0) & (base < np.array(shape) - 1), axis=1)
    base, frac, rgb = base[ok], frac[ok], rgb[ok]
    out = np.zeros((size, 3))
    if len(base) == 0:
        return out.reshape(*shape, 3)
    strides = np.cumprod((1,) + shape[::-1][:-1])[::-1]
    for corner in range(2 ** dims):
        offs = np.array([(corner >> d) & 1 for d in range(dims)])
        w = np.prod(np.where(offs, frac, 1 - frac), axis=1)
        idx = (base + offs) @ strides
        for c in range(3):
            out[:, c] += np.bincount(idx, weights=w * rgb[:, c], minlength=size)
    return out.reshape(*shape, 3)


def sample(grid: np.ndarray, cells: np.ndarray) -> np.ndarray:
    """Read a grid at fractional cell positions"""
    dims = cells.shape[1]
    base = np.floor(cells).astype(int)
    frac = cells - base
    out = np.zeros((len(cells), 3))
    for corner in range(2 ** dims):
        offs = np.array([(corner >> d) & 1 for d in range(dims)])
        w = np.prod(np.where(offs, frac, 1 - frac), axis=1)
        idx = tuple((base + offs).T)
        out += w[:, None] * grid[idx]
    return out


def cap(v: np.ndarray, most: float) -> np.ndarray:
    """Where light piles up, dim the pixel by its brightest channel rather than clipping each one,
    so a crowd of red sparks stays red instead of going white"""
    return v / np.maximum(v.max(axis=1, keepdims=True) / most, 1)


def show(boom: np.ndarray, rest: np.ndarray):
    """Put the glow from bursts and from everything else (0-1 floats) on the active fixture"""
    v = cap(boom * BRIGHTNESS, 1) + cap(rest * BRIGHTNESS, REST_LEVEL ** (1 / GAMMA))
    out = 255 * np.clip(cap(v, 1), 0, 1) ** GAMMA
    f = get_active_fixture()
    f._rgb[:] = out.astype(np.uint8)
    f._changed_arr[:] = True


def motor(burn: float, gravity: float, climb: float) -> float:
    """How hard a rocket's motor has to push so it coasts to a stop climb above where it started.
    climb = a burn^2 / 2 + (a burn)^2 / 2g, solved for a = thrust - gravity"""
    qa, qb, qc = burn * burn / (2 * gravity), burn * burn / 2, -max(0.05, climb)
    return (-qb + math.sqrt(qb * qb - 4 * qa * qc)) / (2 * qa) + gravity


## the hedge: a free 2D sky

class Rocket:
    def __init__(self, u: float, shell: dict, apex: float):
        self.pos = np.array([u, 0.0])
        self.vel = np.array([RNG.normal(0, 0.04), RNG.uniform(0.1, 0.3)])
        self.burn = RNG.uniform(0.25, 0.45)
        self.age = 0.0
        self.shell = shell
        self.fuse = RNG.uniform(-0.04, 0.12)
        """It breaks once it's climbing slower than this, so not always right at the top"""
        self.thrust = motor(self.burn, GRAVITY, apex - 0.02)


class Sky:
    def __init__(self, fixture: Fixture, spark_size: float, aspect: float):
        self.fixture = fixture
        xz = fixture._positions[:, [0, 2]].astype(float)
        lo, hi = xz.min(axis=0), xz.max(axis=0)
        self.h = float(hi[1] - lo[1])
        stretch = aspect * self.h / float(hi[0] - lo[0])
        """The hedge is scanned onto squashed coordinates, this makes round bursts come out round"""
        self.pix = (xz - lo) / self.h
        self.pix[:, 0] *= stretch
        """Pixels in sky heights, x across from the left, y up from the bottom"""
        self.width = float((hi[0] - lo[0]) / self.h * stretch)

        self.cell = spark_size
        self.pad = 3
        self.grid_shape = (int(self.width / self.cell) + 2 * self.pad + 2, int(1 / self.cell) + 2 * self.pad + 2)
        self.pix_cells = self.pix / self.cell + self.pad
        # how bright one unit spark is at its middle once blurred, so it can be undone
        probe = np.zeros(self.grid_shape + (3,))
        probe[self.pad + 2, self.pad + 2] = 1
        self.norm = 1 / blur(blur(probe, 0), 1).max()

        self.sparks = Particles(2)
        self.rockets: list[Rocket] = []
        self.flashes: list[list] = []
        self.ambient = np.zeros(3)
        self.glow_boom = np.zeros((len(self.pix), 3))
        self.glow_rest = np.zeros((len(self.pix), 3))

    def launch(self, shell: dict, u: Optional[float] = None):
        u = float(RNG.uniform(0.12, self.width - 0.12)) if u is None else u
        apex = RNG.uniform(*shell.get("apex", (0.55, 0.85)))
        self.rockets.append(Rocket(u, shell, apex))

    def burst(self, pos: np.ndarray, vel: np.ndarray, shell: dict):
        kind = shell["kind"]
        c1, c2 = shell["c1"], shell["c2"]
        size = shell.get("size", 1.0) * RNG.uniform(0.85, 1.15)
        sp = self.sparks
        inherit = vel * 0.3
        R = 0.32 * size
        """How far the stars travel before drag stops them"""

        def stars(dirs, speed, drag, **kw):
            n = len(dirs)
            v = dirs * (speed * RNG.uniform(0.9, 1.1, n))[:, None] + inherit
            sp.spawn(n, pos=pos, vel=v, drag=drag, boom=1, **kw)

        if kind == "peony":
            n = int(70 * size)
            stars(sphere(n), R * 2.4, 2.4, rgb=c1, life=RNG.uniform(1.3, 2.0, n), grav=0.5, hot=0.12, flick=SPARKLE)
        elif kind == "chrysanthemum":
            n = int(60 * size)
            stars(sphere(n), R * 2.4, 2.4, rgb=c1, life=RNG.uniform(1.4, 2.1, n), grav=0.5, hot=0.12, emit=9)
        elif kind == "ring":
            n = int(44 * size)
            stars(ring(n), R * 2.6, 2.6, rgb=c1, life=RNG.uniform(1.3, 1.7, n), grav=0.4, hot=0.1)
            if RNG.random() < 0.5:  # a little planet in the middle
                stars(sphere(14), R * 0.9, 2.6, rgb=c2, life=1.2, grav=0.4, hot=0.1)
        elif kind == "willow":
            n = int(55 * size)
            stars(sphere(n), R * 1.9, 2.4, rgb=GOLD, life=RNG.uniform(2.8, 3.8, n), grav=1.0, bright=0.8,
                  hot=0.05, emit=14, flick=SPARKLE)
        elif kind == "palm":
            n = int(RNG.integers(6, 10))
            a = np.linspace(0, 2 * math.pi, n, endpoint=False) + RNG.uniform(0, 1)
            dirs = np.stack([np.cos(a), np.sin(a) * 0.8 + 0.25], axis=1)
            stars(dirs, R * 2.8, 1.8, rgb=c1, life=RNG.uniform(1.8, 2.3, n), grav=1.1, bright=1.3, hot=0.1, emit=60)
        elif kind == "crossette":
            n = int(RNG.integers(7, 11))
            a = np.linspace(0, 2 * math.pi, n, endpoint=False) + RNG.uniform(0, 1)
            dirs = np.stack([np.cos(a), np.sin(a)], axis=1)
            stars(dirs, R * 2.0, 2.2, rgb=c1, life=5, grav=0.5, bright=1.1, emit=25,
                  split_t=RNG.uniform(0.45, 0.6, n), split_k=SPLIT_CROSSETTE)
        elif kind == "crackle":
            n = int(55 * size)
            stars(sphere(n), R * 2.2, 2.4, rgb=GOLD, life=5, grav=0.6, bright=0.8, flick=SPARKLE,
                  split_t=RNG.uniform(0.55, 0.9, n), split_k=SPLIT_CRACKLE)
        elif kind == "glitter":
            n = int(70 * size)
            stars(sphere(n), R * 2.2, 2.6, rgb=colour("silver"), life=RNG.uniform(2.0, 2.8, n), grav=0.35,
                  bright=1.1, flick=STROBE)
        elif kind == "double":
            n = int(50 * size)
            stars(sphere(n), R * 2.6, 2.4, rgb=c1, life=RNG.uniform(1.3, 1.8, n), grav=0.5, hot=0.1)
            m = int(30 * size)
            stars(sphere(m), R * 1.2, 2.4, rgb=c2, life=RNG.uniform(1.4, 1.9, m), grav=0.5, hot=0.1, flick=SPARKLE)
        elif kind == "multibreak":
            # a few small shells that go off together round where it broke
            n = int(RNG.integers(3, 6))
            stars(sphere(n), R * 1.6, 3.0, rgb=c1, life=5, bright=0.2, grav=0.4,
                  split_t=RNG.uniform(0.3, 0.5, n), split_k=SPLIT_PEONY)
        elif kind == "kamuro":
            # the big slow gold one
            n = int(110 * size)
            stars(sphere(n), R * 2.1, 2.0, rgb=GOLD, life=RNG.uniform(3.8, 4.8, n), grav=0.9, bright=1.0,
                  hot=0.15, emit=12, flick=SPARKLE)

        c = main_colour(shell)
        self.flashes.append([pos.copy(), c, 0.12 * size, 0.0, 0.18])
        self.ambient = self.ambient + 0.04 * size * c

    def split(self, idx: np.ndarray):
        a = self.sparks.a
        for i in idx:
            pos, vel, rgb, k = a["pos"][i], a["vel"][i], a["rgb"][i], int(a["split_k"][i])
            if k == SPLIT_CROSSETTE:
                ang = RNG.uniform(0, math.pi / 2) + np.arange(4) * math.pi / 2
                dirs = np.stack([np.cos(ang), np.sin(ang)], axis=1)
                self.sparks.spawn(4, pos=pos, vel=dirs * 0.45 + vel * 0.4, rgb=rgb, life=RNG.uniform(0.8, 1.1, 4),
                                  drag=2.4, grav=0.6, hot=0.08, emit=10, boom=1)
            elif k == SPLIT_CRACKLE:
                m = int(RNG.integers(3, 6))
                self.sparks.spawn(m, pos=pos, vel=RNG.normal(0, 0.12, (m, 2)) + vel * 0.3, rgb=WHITE,
                                  life=RNG.uniform(0.15, 0.35, m), drag=4, grav=0.3, flick=CRACKLE, boom=1)
            elif k == SPLIT_PEONY:
                m = 26
                c = random_colour() if RNG.random() < 0.4 else rgb
                v = sphere(m) * 0.4 * RNG.uniform(0.9, 1.1, (m, 1)) + vel * 0.3
                self.sparks.spawn(m, pos=pos, vel=v, rgb=c, life=RNG.uniform(1.0, 1.4, m), drag=2.6, grav=0.5,
                                  hot=0.1, boom=1)
                self.flashes.append([pos.copy(), c, 0.07, 0.0, 0.12])

    def step(self):
        sp = self.sparks
        # rockets: motor on, then coasting
        for r in self.rockets[:]:
            r.age += DT
            acc = np.array([RNG.normal(0, 0.35), -GRAVITY])
            if r.age < r.burn:
                acc[1] += r.thrust
            r.vel += acc * DT
            r.pos += r.vel * DT
            m = int(RNG.integers(1, 4))
            tail = r.shell.get("tail")
            sp.spawn(m, pos=r.pos - r.vel * DT * RNG.random((m, 1)), vel=-r.vel * 0.12 + RNG.normal(0, 0.06, (m, 2)),
                     rgb=GOLD if tail is None else tail, life=RNG.uniform(0.25, 0.55, m), drag=3, grav=0.6,
                     bright=0.7, flick=SPARKLE)
            if r.age > r.burn and r.vel[1] < r.fuse:
                self.rockets.remove(r)
                self.burst(r.pos, r.vel, r.shell)

        sp.flush()
        a = sp.a
        n = len(sp)
        if n:
            a["age"] += DT
            a["vel"] *= np.exp(-a["drag"] * DT)[:, None]
            a["vel"][:, 1] -= GRAVITY * a["grav"] * DT
            a["pos"] += a["vel"] * DT

            # embers shed off comets and willows, hanging nearly still
            if n < MAX_PARTICLES:
                live = 1 - a["age"] / a["life"]
                idx = np.nonzero(RNG.random(n) < a["emit"] * DT * live)[0]
                if len(idx):
                    m = len(idx)
                    sp.spawn(m, pos=a["pos"][idx], vel=a["vel"][idx] * 0.08 + RNG.normal(0, 0.02, (m, 2)),
                             rgb=a["rgb"][idx] * 0.5 + GOLD * 0.5, life=RNG.uniform(0.3, 0.8, m), drag=4, grav=0.25,
                             bright=0.45 * a["bright"][idx] * live[idx], flick=SPARKLE)

            due = a["age"] >= a["split_t"]
            if np.any(due):
                self.split(np.nonzero(due)[0])
            p = a["pos"]
            alive = (a["age"] < a["life"]) & ~due & (p[:, 1] > -0.3) & (p[:, 0] > -0.5) & (p[:, 0] < self.width + 0.5)
            sp.keep(alive)

        for f in self.flashes:
            f[3] += DT
        self.flashes = [f for f in self.flashes if f[3] < f[4]]
        self.ambient *= math.exp(-DT / 0.3)

    def render(self):
        sp = self.sparks
        rgb, level = sp.light() if len(sp) else (np.zeros((0, 3)), np.zeros(0))
        pos = sp.a["pos"]
        boom = sp.a["boom"] > 0
        if self.rockets:
            heads = np.array([r.pos for r in self.rockets])
            pos = np.concatenate([pos, heads])
            rgb = np.concatenate([rgb, np.tile((1.0, 0.85, 0.6), (len(heads), 1))])
            level = np.concatenate([level, np.full(len(heads), 1.3)])
            boom = np.concatenate([boom, np.zeros(len(heads), dtype=bool)])

        def light_of(mask):
            grid = splat(self.grid_shape, pos[mask] / self.cell + self.pad, rgb[mask] * level[mask, None])
            return sample(blur(blur(grid, 0), 1) * self.norm, self.pix_cells)

        bursts, rest = light_of(boom), light_of(~boom)
        for pos_f, c, radius, age, dur in self.flashes:
            d2 = np.sum((self.pix - pos_f) ** 2, axis=1)
            bursts += (1.1 * (1 - age / dur) ** 2 * np.exp(-d2 / (2 * radius * radius)))[:, None] * (c * 0.8 + 0.2)
        rest += self.ambient

        self.glow_boom = np.maximum(self.glow_boom * TRAIL_DECAY, bursts)
        self.glow_rest = np.maximum(self.glow_rest * TRAIL_DECAY, rest)
        show(self.glow_boom, self.glow_rest)

    def draw(self):
        while True:
            self.step()
            self.render()
            yield


## the front and the fence: sparks running along wires

class WireRocket:
    def __init__(self, edge: int, shell: dict, thrust: float, burn: float, drag: float, climb: bool, fuse: float):
        self.e = edge
        self.s = 0.0
        self.v = RNG.uniform(0.3, 0.8)
        self.age = 0.0
        self.shell = shell
        self.thrust = thrust
        self.burn = burn
        self.drag = drag
        self.climb = climb
        """Climbing rockets only take edges going up, and burst when there aren't any. The rest go straight on"""
        self.fuse = fuse
        self.travelled = 0.0
        self.target = np.inf
        """Flat rockets burst once they've gone this far"""


class Wire:
    def __init__(self, fixture: Graph, radius: float, launch_corners: bool = False):
        self.fixture = fixture
        P = fixture._positions.astype(float)
        self.P = P
        N = self.n = len(P)

        # pixel neighbours along the wires, pixels sharing a corner are neighbours too
        self.adj = [[p.id for p in fixture.neighbours(i)] for i in range(N)]
        self.A = np.zeros((N, N))
        for i, ns in enumerate(self.adj):
            self.A[i, ns] = 1

        # directed edges between neighbouring pixels
        eid: dict[tuple[int, int], int] = {}
        ef, et = [], []
        for a in range(N):
            for b in self.adj[a]:
                eid[(a, b)] = len(ef)
                ef.append(a)
                et.append(b)
        self.eid = eid
        self.ef, self.et = np.array(ef), np.array(et)
        vec = P[self.et] - P[self.ef]
        norm = np.linalg.norm(vec, axis=1)
        self.edir = vec / np.maximum(norm, 1e-9)[:, None]
        self.elen = np.maximum(norm, 0.02)
        self.rev = np.array([eid[(b, a)] for a, b in zip(ef, et)])
        self.succ = [[eid[(b, c)] for c in self.adj[b] if c != a] for a, b in zip(ef, et)]
        self.nsucc = np.array([len(s) for s in self.succ])
        self.succ1 = np.array([s[0] if s else -1 for s in self.succ])
        self.out = [[eid[(a, b)] for b in self.adj[a]] for a in range(N)]

        self.radius = radius
        """How far a burst's shell spreads, metres"""

        # the bottoms of vertical runs near the ground, for rockets to go up from
        self.corners: list[int] = []
        self.climb: dict[int, float] = {}
        if launch_corners:
            used: set[int] = set()
            """Vertices with a corner already, a corner with several pixels launches from one of them"""
            for i in range(N):
                vertex = fixture.vertex_of(i)
                if vertex is not None and vertex.id in used:
                    continue
                dz = [self.edir[e, 2] for e in self.out[i]]
                if P[i, 2] < 1 and max(dz) > 0.9 and min(dz) > -0.1:
                    if vertex is not None:
                        used.add(vertex.id)
                    up = max(self.out[i], key=lambda e: self.edir[e, 2] * min(self.elen[e], 0.08))
                    e, h = up, 0.0
                    for _ in range(N):
                        h += self.edir[e, 2] * self.elen[e]
                        nxt = self.rocket_next(e, True)
                        if nxt is None:
                            break
                        e = nxt
                    self.corners.append(i)
                    self.climb[i] = h
            self.corners.sort(key=lambda i: P[i, 0])
            """Left to right"""

        self.sparks = Particles(1)
        self.rockets: list[WireRocket] = []
        self.fronts: list[dict] = []
        self.flashes: list[list] = []
        self.fountains: list[dict] = []
        self.t = 0.0
        self.glow_boom = np.zeros((N, 3))
        self.glow_rest = np.zeros((N, 3))

    ## places on the wire

    def point(self, e: int, s: float) -> np.ndarray:
        f = min(1.0, max(0.0, s / self.elen[e]))
        return self.P[self.ef[e]] * (1 - f) + self.P[self.et[e]] * f

    def edge_from(self, pixel: int, direction: int) -> int:
        """The edge out of a pixel towards the next (+1) or previous (-1) pixel along the strip"""
        outs = self.out[pixel]
        for e in outs:
            if self.et[e] == pixel + direction:
                return e
        return outs[int(RNG.integers(len(outs)))]

    def rocket_next(self, e: int, climb: bool) -> Optional[int]:
        choices = self.succ[e]
        if not choices:
            return None
        if climb:
            best = max(choices, key=lambda c: self.edir[c, 2] * min(self.elen[c], 0.08))
            return best if self.edir[best, 2] > 0.5 else None
        best = max(choices, key=lambda c: float(self.edir[c] @ self.edir[e]))
        return best if float(self.edir[best] @ self.edir[e]) > -0.5 else None

    ## what the director asks for

    def launch_climb(self, shell: dict, corner: Optional[int] = None):
        """A rocket up the wall from a bottom corner"""
        corner = self.corners[int(RNG.integers(len(self.corners)))] if corner is None else corner
        e = max(self.out[corner], key=lambda e: self.edir[e, 2] * min(self.elen[e], 0.08))
        # aim somewhere up the climb, past the top means it bursts at the top corner
        target = self.climb[corner] * RNG.uniform(0.65, 1.2)
        burn = RNG.uniform(0.25, 0.4)
        self.rockets.append(WireRocket(e, shell, motor(burn, WIRE_GRAVITY, target), burn, 0.0, True,
                                       RNG.uniform(0.0, 0.4)))
        self.flashes.append([self.P[corner].copy(), np.array((1.0, 0.8, 0.5)), 0.25, 0.0, 0.15, False])

    def launch_end(self, shell: dict, from_start: Optional[bool] = None):
        """A rocket fired from one end of the wire that bursts near or past the middle"""
        from_start = RNG.random() < 0.5 if from_start is None else from_start
        at, direction = (0, 1) if from_start else (self.n - 1, -1)
        length = float(self.elen[self.ef != self.et].sum() / 2)
        """Each pixel to pixel step is in elen twice, once each way"""
        target = length * RNG.uniform(0.4, 0.8)
        burn, drag = RNG.uniform(0.3, 0.45), 0.6
        # enough motor that drag won't stop it short: coasting goes about v / drag
        top = 1.15 * target * drag
        r = WireRocket(self.edge_from(at, direction), shell, top / burn + drag * top / 2, burn, drag, False, 1.0)
        r.target = target
        self.rockets.append(r)
        self.flashes.append([self.P[at].copy(), np.array((1.0, 0.6, 0.2)), 0.35, 0.0, 0.2, False])

    def sprinkler(self, along: float, length: float):
        """Sprays flames both ways along the wire from one spot"""
        self.fountains.append({"p": int(along * (self.n - 1)), "age": 0.0, "length": length,
                               "rate": RNG.uniform(90, 150), "speed": RNG.uniform(2.0, 3.5)})

    def spawn_sparks(self, edges, s, v, spec: dict):
        n = len(edges)
        if n == 0 or len(self.sparks) > MAX_WIRE_PARTICLES:
            return
        self.sparks.spawn(n, edge=np.asarray(edges, float), pos=np.asarray(s, float)[:, None],
                          vel=np.asarray(v, float)[:, None], **resolve(spec, n))

    ## shells

    def burst(self, e: int, s: float, shell: dict):
        kind, c1, c2 = shell["kind"], shell["c1"], shell["c2"]
        size = shell.get("size", 1.0) * RNG.uniform(0.85, 1.15)
        pos = self.point(e, s)
        R = self.radius * size
        main = c1
        """Bursts on the house are always in colour"""

        # what the sparks the shell lights on the wire are like
        spark = {"rgb": main, "life": (1.1, 1.8), "drag": 1.6, "grav": 1.0, "bright": 1.0, "flick": SPARKLE,
                 "hot": 0.04, "branch": 1, "boom": 1}
        ignite = 0.22
        """Chance each pixel the shell passes over starts a spark"""
        fronts = [(pos, R, main, 1.0, 0.0, 0.35)]
        """Expanding shells: centre, radius, colour, brightness, delay, thickness"""
        local, speed = 6, 1.0
        """Sparks thrown along the wire right where it burst"""

        if kind == "chrysanthemum":
            spark["emit"] = 8
        elif kind == "ring":
            ignite, local = 0.06, 4
            fronts = [(pos, R * 1.1, c1, 1.7, 0.0, 0.18)]
        elif kind in ("willow", "kamuro"):
            big = 1.3 if kind == "kamuro" else 1.0
            spark.update(life=(2.4, 3.4), drag=1.0, grav=1.3, bright=0.85, emit=8)
            ignite, local = 0.35, 8
            fronts = [(pos, R * big, main, 0.8, 0.0, 0.4)]
        elif kind == "palm":
            spark.update(life=(1.6, 2.2), drag=0.9, emit=40, bright=1.3, branch=3, flick=STEADY)
            ignite, local, speed = 0.08, 6, 1.5
        elif kind == "crossette":
            spark.update(split_t=(0.35, 0.55), split_k=SPLIT_CROSSETTE, branch=2)
            ignite = 0.2
        elif kind == "crackle":
            spark.update(split_t=(0.4, 0.8), split_k=SPLIT_CRACKLE)
            ignite = 0.3
        elif kind == "glitter":
            spark.update(life=(1.8, 2.5), flick=STROBE, drag=2.0, grav=0.5)
            fronts = [(pos, R, main, 0.6, 0.0, 0.35)]
            ignite = 0.3
        elif kind == "double":
            fronts = [(pos, R * 1.1, c1, 1.0, 0.0, 0.3), (pos, R * 0.55, c2, 1.0, 0.1, 0.3)]
        elif kind == "multibreak":
            fronts, local = [], 3
            for _ in range(int(RNG.integers(3, 5))):
                at = pos + np.array([RNG.normal(0, 0.8), 0, RNG.normal(0, 0.6)]) * size
                fronts.append((at, R * 0.45, bright_colour() if RNG.random() < 0.5 else c1, 1.2,
                               RNG.uniform(0.25, 0.5), 0.25))

        for centre, radius, c, bright, delay, width in fronts:
            self.fronts.append({"c": centre, "d": np.linalg.norm(self.P - centre, axis=1), "R": radius, "k": 2.4,
                                "rgb": np.asarray(c, float), "bright": bright, "age": -delay, "life": 1.4,
                                "w": width, "ignite": ignite, "spark": dict(spark, rgb=c) if kind != "palm" else spark,
                                "prev": 0.0})

        # sparks thrown both ways along the wire from the burst
        forward = RNG.random(local) < 0.5
        edges = np.where(forward, e, self.rev[e])
        ss = np.where(forward, s, self.elen[e] - s)
        self.spawn_sparks(edges, ss, R * 2.0 * speed * RNG.uniform(0.5, 1.0, local), spark)

        self.flashes.append([pos, main, 0.45 * size, 0.0, 0.2, True])

    def burst_flat(self, e: int, s: float, shell: dict):
        """A fence burst: a flash, then sparks thrown out fast both ways that drag slows to a stop as they burn out"""
        size = shell.get("size", 1.0) * RNG.uniform(0.85, 1.15)
        n = int(RNG.integers(24, 38) * size)
        c = shell["c1"]
        top = RNG.uniform(6, 9) * size
        forward = RNG.random(n) < 0.5
        edges = np.where(forward, e, self.rev[e])
        ss = np.where(forward, s, self.elen[e] - s)
        speeds = top * RNG.uniform(0.15, 1.0, n) ** 0.7
        spark = {"rgb": c, "life": (0.9, 1.7), "drag": 2.2, "grav": 1.0, "bright": 1.1, "flick": SPARKLE,
                 "hot": 0.08, "boom": 1, "fire": (RNG.random(n) < 0.4).astype(float)}
        if shell["kind"] == "crackle":
            spark.update(split_t=(0.5, 0.9), split_k=SPLIT_CRACKLE)
        elif shell["kind"] in ("willow", "kamuro"):
            spark.update(life=(1.8, 2.6), drag=1.4, emit=10, fire=1.0)
        self.spawn_sparks(edges, ss, speeds, spark)
        self.flashes.append([self.point(e, s), c, 0.6 * size, 0.0, 0.22, True])

    ## physics

    def step_rockets(self):
        for r in self.rockets[:]:
            r.age += DT
            acc = -WIRE_GRAVITY * self.edir[r.e, 2] - r.drag * r.v
            if r.age < r.burn:
                acc += r.thrust
            r.v += acc * DT
            r.s += r.v * DT
            r.travelled += r.v * DT
            done = (r.age > r.burn and r.v < r.fuse) or r.travelled >= r.target
            while not done and r.s >= self.elen[r.e]:
                nxt = self.rocket_next(r.e, r.climb)
                if nxt is None:
                    r.s = float(self.elen[r.e])
                    done = True
                else:
                    r.s -= self.elen[r.e]
                    r.e = nxt
            # the tail it leaves, sparks sliding back down behind it
            m = int(RNG.integers(2, 4))
            self.sparks.spawn(m, edge=self.rev[r.e], pos=np.full((m, 1), max(0.0, self.elen[r.e] - r.s)),
                              vel=RNG.uniform(0, 0.6, (m, 1)), rgb=GOLD, life=RNG.uniform(0.25, 0.6, m), drag=4,
                              grav=0.3, bright=0.9, flick=SPARKLE, fire=1)
            if done:
                self.rockets.remove(r)
                at = max(0.0, min(r.s, float(self.elen[r.e])))
                (self.burst if r.climb else self.burst_flat)(r.e, at, r.shell)

    def step_fronts(self):
        for f in self.fronts:
            f["age"] += DT
            if f["age"] < 0:
                continue
            r = f["R"] * (1 - math.exp(-f["k"] * f["age"]))
            if f["ignite"] > 0:
                idx = np.nonzero((f["d"] >= f["prev"]) & (f["d"] < r))[0]
                idx = idx[RNG.random(len(idx)) < f["ignite"]]
                if len(idx):
                    shell_speed = f["R"] * f["k"] * math.exp(-f["k"] * f["age"])
                    edges, speeds = [], []
                    for i in idx:
                        # the star flies on away from the burst, along whichever way the wire goes
                        radial = (self.P[i] - f["c"]) / max(f["d"][i], 1e-3)
                        outs = self.out[i]
                        dots = self.edir[outs] @ radial
                        j = int(np.argmax(dots))
                        if dots[j] > 0.25:
                            edges.append(outs[j])
                            speeds.append(shell_speed * dots[j] * RNG.uniform(0.8, 1.1) + 0.3)
                    self.spawn_sparks(edges, np.zeros(len(edges)), speeds, f["spark"])
            f["prev"] = r
        self.fronts = [f for f in self.fronts if f["age"] < f["life"]]

    def step_fountains(self):
        for f in self.fountains:
            f["age"] += DT
            # swells up, roars, then sputters out
            env = min(1, f["age"] / 0.6) * min(1, (f["length"] - f["age"]) / 1.2)
            m = RNG.poisson(f["rate"] * DT * max(env, 0))
            if m:
                outs = self.out[f["p"]]
                edges = [outs[int(k)] for k in RNG.integers(0, len(outs), m)]
                self.spawn_sparks(edges, np.zeros(m), RNG.uniform(0.2, 1.0, m) * f["speed"],
                                  {"rgb": GOLD, "life": (0.35, 1.0), "drag": 2.5, "grav": 1.0, "bright": 1.0,
                                   "fire": 1, "flick": np.where(RNG.random(m) < 0.06, CRACKLE, SPARKLE)})
        self.fountains = [f for f in self.fountains if f["age"] < f["length"]]

    def step(self):
        self.t += DT
        self.step_rockets()
        self.step_fronts()
        self.step_fountains()

        sp = self.sparks
        sp.flush()
        a = sp.a
        n = len(sp)
        if n:
            e = a["edge"].astype(int)
            s = a["pos"][:, 0]
            v = a["vel"][:, 0]
            a["age"] += DT
            v *= np.exp(-a["drag"] * DT)
            v -= WIRE_GRAVITY * a["grav"] * self.edir[e, 2] * DT
            s += v * DT

            # going backwards (thrown up a wall and falling back), so turn round onto the reverse edge
            back = v < 0
            if np.any(back):
                e[back] = self.rev[e[back]]
                s[back] = self.elen[e[back]] - s[back]
                v[back] = -v[back]

            # run on past the end of the edge onto the next one
            dead = np.zeros(n, dtype=bool)
            for _ in range(16):
                over = np.nonzero((s >= self.elen[e]) & ~dead)[0]
                if len(over) == 0:
                    break
                s[over] -= self.elen[e[over]]
                count = self.nsucc[e[over]]
                one = over[count == 1]
                e[one] = self.succ1[e[one]]
                dead[over[count == 0]] = True
                for i in over[count >= 2]:
                    # a junction: pick a way, and maybe split down the others too
                    choices = self.succ[e[i]]
                    pick = int(RNG.integers(len(choices)))
                    if a["branch"][i] > 0:
                        for k, other in enumerate(choices):
                            if k != pick:
                                sp.clone(i, edge=other, pos=[s[i]], vel=[v[i] * 0.9], branch=a["branch"][i] - 1)
                        a["branch"][i] -= 1
                    e[i] = choices[pick]
            a["edge"] = e.astype(float)

            # embers dropped by willows and palms
            if n < MAX_WIRE_PARTICLES:
                live = 1 - a["age"] / a["life"]
                idx = np.nonzero(RNG.random(n) < a["emit"] * DT * live)[0]
                if len(idx):
                    m = len(idx)
                    sp.spawn(m, edge=e[idx], pos=s[idx, None], vel=np.zeros((m, 1)),
                             rgb=a["rgb"][idx] * 0.5 + GOLD * 0.5, life=RNG.uniform(0.3, 0.8, m), drag=4, grav=0.3,
                             bright=0.5 * a["bright"][idx] * live[idx], flick=SPARKLE)

            for i in np.nonzero(a["age"] >= a["split_t"])[0]:
                if a["split_k"][i] == SPLIT_CRACKLE:
                    a["flick"][i] = CRACKLE
                    a["rgb"][i] = WHITE
                    a["life"][i] = a["age"][i] + RNG.uniform(0.3, 0.6)
                else:
                    # crossette: half of it goes back the way it came
                    sp.clone(i, edge=self.rev[e[i]], pos=[self.elen[e[i]] - s[i]], split_t=np.inf, hot=0.08,
                             age=0.0, life=RNG.uniform(0.8, 1.2))
                    a["hot"][i], a["age"][i], a["life"][i] = 0.08, 0.0, RNG.uniform(0.8, 1.2)
                a["split_t"][i] = np.inf

            sp.keep((a["age"] < a["life"]) & ~dead)

        for f in self.flashes:
            f[3] += DT
        self.flashes = [f for f in self.flashes if f[3] < f[4]]

    def render(self):
        N = self.n
        sp = self.sparks
        e = sp.a["edge"].astype(int)
        s = sp.a["pos"][:, 0]
        boom = sp.a["boom"] > 0
        cols = np.zeros((0, 3))
        if len(sp):
            rgb, level = sp.light()
            cols = rgb * level[:, None]
        if self.rockets:
            e = np.concatenate([e, [r.e for r in self.rockets]])
            s = np.concatenate([s, [r.s for r in self.rockets]])
            cols = np.concatenate([cols, np.tile((1.3, 0.8, 0.3), (len(self.rockets), 1))])
            boom = np.concatenate([boom, np.zeros(len(self.rockets), dtype=bool)])
        f = np.clip(s / self.elen[e], 0, 1) if len(e) else np.zeros(0)

        def light_of(mask):
            light = np.zeros((N, 3))
            for c in range(3):
                light[:, c] += np.bincount(self.ef[e[mask]], weights=(1 - f[mask]) * cols[mask, c], minlength=N)
                light[:, c] += np.bincount(self.et[e[mask]], weights=f[mask] * cols[mask, c], minlength=N)
            return light + 0.35 * self.A @ light

        bursts, light = light_of(boom), light_of(~boom)

        for fr in self.fronts:
            if fr["age"] < 0:
                continue
            r = fr["R"] * (1 - math.exp(-fr["k"] * fr["age"]))
            level = fr["bright"] * (1 - fr["age"] / fr["life"]) ** 1.5
            bursts += (level * np.exp(-((fr["d"] - r) / fr["w"]) ** 2))[:, None] * fr["rgb"]

        for pos, c, radius, age, dur, is_burst in self.flashes:
            d2 = np.sum((self.P - pos) ** 2, axis=1)
            flash = (1.1 * (1 - age / dur) ** 2 * np.exp(-d2 / (2 * radius * radius)))[:, None] * (c * 0.8 + 0.2)
            if is_burst:
                bursts += flash
            else:
                light += flash

        self.glow_boom = np.maximum(self.glow_boom * WIRE_TRAIL_DECAY, bursts)
        self.glow_rest = np.maximum(self.glow_rest * WIRE_TRAIL_DECAY, light)
        show(self.glow_boom, self.glow_rest)

    def draw(self):
        while True:
            self.step()
            self.render()
            yield


FENCE = Wire(fence_graph, radius=1.8)
HEDGE = Sky(hedge_wall, spark_size=0.05, aspect=16 / 9)
"""The hedge is scanned onto -1 to 1 by 0 to 0.54 but is really 16:9"""
FRONT = Wire(front_graph, radius=2.0, launch_corners=True)


## shells

SHELLS = ["peony", "chrysanthemum", "ring", "willow", "palm", "crossette", "crackle", "glitter", "double", "multibreak"]
SHELL_WEIGHTS = [3, 2, 1.5, 1.5, 1, 1, 1.2, 1, 1.2, 0.8]
BIG_SHELLS = ["peony", "crackle", "willow", "glitter", "palm", "chrysanthemum"]
BIG_WEIGHTS = [2, 2, 2, 2, 1, 1]


def make_shell(kind: Optional[str] = None, big: bool = False, c1: Optional[np.ndarray] = None) -> dict:
    if kind is None:
        names, weights = (BIG_SHELLS, BIG_WEIGHTS) if big else (SHELLS, SHELL_WEIGHTS)
        w = np.array(weights, dtype=float)
        kind = str(RNG.choice(names, p=w / w.sum()))
    c1 = random_colour() if c1 is None else c1
    shell = {"kind": kind, "c1": c1, "c2": random_colour(), "size": float(RNG.uniform(0.8, 1.2))}
    if RNG.random() < 0.25:
        shell["tail"] = c1 * 0.6 + 0.4
    return shell


def hedge(shell: Optional[dict] = None, u: Optional[float] = None):
    HEDGE.launch(shell or make_shell(), u)


def front(shell: Optional[dict] = None, corner: Optional[int] = None):
    """corner is 0-3, left to right. Bursts on the house are always in a proper colour, never gold or silver"""
    shell = dict(shell or make_shell())
    if any(np.allclose(shell["c1"], colour(n)) for n in ("gold", "silver")):
        shell["c1"] = bright_colour()
    FRONT.launch_climb(shell, None if corner is None else FRONT.corners[corner])


def fence(from_start: Optional[bool] = None, kind: Optional[str] = None, c: Optional[np.ndarray] = None):
    """A rocket from one end of the fence, in fire colours"""
    kind = kind or str(RNG.choice(["peony", "peony", "crackle", "willow"]))
    FENCE.launch_end(make_shell(kind, c1=fire_colour() if c is None else c), from_start)


def anywhere(shell: Optional[dict] = None):
    """Mostly the hedge, the house is easily crowded"""
    (hedge if RNG.random() < 0.75 else front)(shell)


## segments: scripts the director picks from, yielding seconds to wait

Segment = Iterator[float]


def seg_singles() -> Segment:
    for _ in range(int(RNG.integers(4, 9))):
        anywhere()
        yield RNG.uniform(0.9, 2.4)


def seg_pairs() -> Segment:
    """The hedge and the house fire the same shell together"""
    for _ in range(int(RNG.integers(3, 6))):
        shell = make_shell()
        hedge(shell)
        if RNG.random() < 0.5:
            front(shell)
        yield RNG.uniform(1.8, 3.2)


def seg_hedge_sweep() -> Segment:
    """Shells walking across the hedge, then the house answers"""
    for sweep in range(int(RNG.integers(2, 4))):
        shell = make_shell()
        n = int(RNG.integers(4, 8))
        us = list(np.linspace(0.2, HEDGE.width - 0.2, n) + RNG.normal(0, 0.04, n))
        if (sweep + RNG.integers(2)) % 2:
            us.reverse()
        gap = RNG.uniform(0.12, 0.3)
        for i, u in enumerate(us):
            s = dict(shell, size=shell["size"] * 0.8)
            if RNG.random() < 0.3:
                s["c1"] = shell["c2"] if i % 2 else shell["c1"]
            hedge(s, float(u))
            yield gap
        yield 0.5
        if RNG.random() < 0.5:
            front(shell)
        yield RNG.uniform(1.5, 2.5)


def seg_corners() -> Segment:
    """Rockets up the corners of the door and window, a pair at a time, with the hedge filling in"""
    order = [[0, 3], [1, 2]] if RNG.random() < 0.5 else [[1, 2], [0, 3]]
    if RNG.random() < 0.4:
        order = [[0], [1], [2], [3]] if RNG.random() < 0.5 else [[3], [2], [1], [0]]
    shell = make_shell()
    for group in order:
        for c in group:
            front(shell, c)
        yield RNG.uniform(1.6, 2.4)
        if RNG.random() < 0.5:
            hedge()
            yield RNG.uniform(0.8, 1.4)
    yield 2.0


def seg_call_and_response() -> Segment:
    """Hedge, then house, then fence, the same colour each time"""
    for _ in range(int(RNG.integers(3, 5))):
        shell = make_shell()
        hedge(shell)
        yield RNG.uniform(0.7, 1.1)
        front(shell)
        yield RNG.uniform(0.5, 0.9)
        fence()
        yield RNG.uniform(1.5, 2.5)


def seg_rainbow() -> Segment:
    names = BRIGHT_COLOURS if RNG.random() < 0.5 else BRIGHT_COLOURS[::-1]
    kind = str(RNG.choice(["peony", "ring", "double", "chrysanthemum"]))
    us = np.linspace(0.15, HEDGE.width - 0.15, len(names))
    for i, cname in enumerate(names):
        shell = make_shell(kind, c1=colour(cname))
        if i % 4 == 3:
            front(shell)
        else:
            hedge(shell, float(us[i]))
        yield RNG.uniform(0.3, 0.6)
    yield 2.0


def seg_willow_drift() -> Segment:
    """Slow gold, the calm bit"""
    for _ in range(int(RNG.integers(4, 7))):
        if RNG.random() < 0.8:
            hedge(make_shell(str(RNG.choice(["willow", "kamuro"]))))
        else:
            front(make_shell("willow"))
        yield RNG.uniform(1.8, 3.0)


def seg_crackle_storm() -> Segment:
    for _ in range(int(RNG.integers(8, 13))):
        anywhere(make_shell(str(RNG.choice(["crackle", "glitter", "crackle", "palm"]))))
        yield RNG.uniform(0.18, 0.45)
    yield 2.5


def seg_barrage() -> Segment:
    """Everything at once, building to one huge volley, then a breath"""
    length = RNG.uniform(10, 14)
    DIRECTOR.spawn(fence_barrage(length))
    t = 0.0
    while t < length:
        hedge(make_shell(big=True)) if RNG.random() < 0.85 else front(make_shell(big=True))
        gap = RNG.uniform(0.12, 0.5) * (1 - 0.7 * t / length)
        yield gap
        t += gap
    for i in range(8):
        hedge(make_shell(str(RNG.choice(["kamuro", "crackle", "glitter"]))), 0.15 + (HEDGE.width - 0.3) * i / 7)
        yield RNG.uniform(0, 0.06)
    for c in (0, len(FRONT.corners) - 1):
        front(make_shell(str(RNG.choice(["kamuro", "crackle"]))), c)
    yield 7.0


def seg_breather() -> Segment:
    if RNG.random() < 0.5:
        anywhere(make_shell(str(RNG.choice(["glitter", "willow", "ring"]))))
    yield RNG.uniform(3, 6)


def fseg_volley() -> Segment:
    """Rockets from whichever end"""
    for _ in range(int(RNG.integers(3, 6))):
        fence()
        yield RNG.uniform(1.0, 2.4)


def fseg_converge() -> Segment:
    """From both ends at once, meeting round the middle"""
    for _ in range(int(RNG.integers(1, 3))):
        c = fire_colour()
        fence(True, c=c)
        fence(False, c=c)
        yield RNG.uniform(2.8, 3.8)


def fseg_chase() -> Segment:
    """A run of rockets all from one end"""
    from_start = RNG.random() < 0.5
    for _ in range(int(RNG.integers(3, 6))):
        fence(from_start)
        yield RNG.uniform(0.4, 0.8)
    yield 2.0


def fseg_sprinklers() -> Segment:
    length = RNG.uniform(4, 7)
    n = int(RNG.integers(1, 4))
    for x in np.linspace(0.2, 0.8, n) if n > 1 else [RNG.uniform(0.3, 0.7)]:
        FENCE.sprinkler(float(x + RNG.normal(0, 0.04)), length)
    yield length + 0.5


def fseg_rest() -> Segment:
    yield RNG.uniform(2, 5)


def fence_barrage(length: float) -> Segment:
    """Runs alongside seg_barrage"""
    for x in (0.2, 0.5, 0.8):
        FENCE.sprinkler(x, length + 2)
    t = 0.0
    while t < length:
        fence()
        gap = RNG.uniform(0.5, 1.1)
        yield gap
        t += gap


SEGMENTS: dict[str, tuple[Callable[[], Segment], float, int]] = {
    # name: (script, how often, how intense 0-3)
    "singles": (seg_singles, 3, 1),
    "pairs": (seg_pairs, 2, 1),
    "hedge sweep": (seg_hedge_sweep, 2, 2),
    "corners": (seg_corners, 2, 2),
    "call and response": (seg_call_and_response, 1.5, 1),
    "rainbow": (seg_rainbow, 1.5, 2),
    "willow drift": (seg_willow_drift, 1.5, 0),
    "crackle storm": (seg_crackle_storm, 1.2, 2),
    "barrage": (seg_barrage, 0.5, 3),
    "breather": (seg_breather, 1, 0),
}
FENCE_SEGMENTS: dict[str, tuple[Callable[[], Segment], float, int]] = {
    "volley": (fseg_volley, 3, 1),
    "converge": (fseg_converge, 2, 1),
    "chase": (fseg_chase, 1.5, 2),
    "sprinklers": (fseg_sprinklers, 1.5, 1),
    "rest": (fseg_rest, 1.5, 0),
}
TRACKS = {"sky": SEGMENTS, "fence": FENCE_SEGMENTS}
BARRAGE_EVERY = 70
"""Seconds before a barrage can come round again, after that it gets more likely the longer it's been"""


class Director:
    """Runs segments forever, picking the next at random whenever a track's one finishes"""

    def __init__(self):
        self.t = 0.0
        self.tasks: list[list] = []
        """[when it next runs, the segment, its track or None for helpers]"""
        self.recent: dict[str, list[str]] = {track: [] for track in TRACKS}
        self.last_barrage = 0.0

    def spawn(self, segment: Segment, track: Optional[str] = None):
        self.tasks.append([self.t, segment, track])

    def pick(self, track: str):
        library = TRACKS[track]
        recent = self.recent[track]
        if not recent and track == "sky":
            name = "singles"
        elif recent and track == "sky" and library[recent[-1]][2] >= 2 and RNG.random() < 0.4:
            name = "breather"
        else:
            names, weights = [], []
            for n, (_, w, _) in library.items():
                if n in recent[-2:]:
                    continue
                if n == "barrage":
                    since = self.t - self.last_barrage
                    if since < BARRAGE_EVERY:
                        continue
                    w += (since - BARRAGE_EVERY) / 25
                names.append(n)
                weights.append(w)
            p = np.array(weights) / sum(weights)
            name = str(RNG.choice(names, p=p))
        if name == "barrage":
            self.last_barrage = self.t
        recent.append(name)
        del recent[:-4]
        print(f"[fireworks] {track}: {name}")
        self.spawn(library[name][0](), track)

    def tick(self, t: float):
        self.t = t
        for track in TRACKS:
            if not any(task[2] == track for task in self.tasks):
                self.pick(track)
        for task in self.tasks[:]:
            for _ in range(50):
                if task[0] > t:
                    break
                try:
                    task[0] = t + next(task[1])
                except StopIteration:
                    self.tasks.remove(task)
                    break


DIRECTOR = Director()


def display_update():
    for fixture, draw in ((fence_graph, FENCE.draw), (front_graph, FRONT.draw), (hedge_wall, HEDGE.draw)):
        fixture.set_draw_fn(draw)
    DIRECTOR.tick(frame() / DISPLAY_TICK_FPS)
