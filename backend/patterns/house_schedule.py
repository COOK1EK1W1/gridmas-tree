"""The house's 24/7 show, picked by the time of day (atlas's local time).

  04:00 - 16:00  off
  16:00 - 21:00  random patterns, a new one every SLOT_SECONDS
  21:00 - 04:00  starry night: still, softly twinkling stars everywhere and the odd
                 shooting star streaking along the fence

Random patterns work like --auto-pattern: every pattern file in this directory is a
candidate unless it's in EXCLUDE, is a display (has a display_update()) or uses music.
Each slot one is picked at random (not one of the last few) and its draw() is imported
fresh for every fixture of the house, so each runs its own copy.

Patterns written for the tree expect tree coordinates (x and y -1 to 1, z 0 to 4), so
they draw on a stand-in Volume of each fixture squashed into the tree's box and the
colours are copied across. Graph patterns (ones with a draw_graph()) draw straight on
the fence and front of the house. A pattern that crashes is dropped until restart.

Run it all day with: main.py --idle-pattern house_schedule
"""

import datetime
import importlib.util
import math
import os
import random
import sys
import traceback
from typing import Callable, Optional

import numpy as np

import attribute
import house_fixtures
from fixture import Fixture, Graph, Volume, get_active_fixture, setActiveFixture
from house_fixtures import attach, fence_graph, front_graph, hedge_wall
from gridmas import *

name = "House Schedule"
author = "Ciaran"

FPS = 45

## schedule, in hours of the local day

RANDOM_FROM = 16
STARRY_FROM = 21
STARRY_UNTIL = 4
"""Off from STARRY_UNTIL until RANDOM_FROM"""

## random patterns

SLOT_SECONDS = 90
"""How long each random pattern runs for"""
NO_REPEAT = 8
"""Don't pick any of the last this many patterns again"""
RANDOM_BRIGHTNESS = 1.0

EXCLUDE = {
    # tools, not shows
    "Calibrate", "Center Finder", "Graph Check", "off", "on", "Solid Color", "Strip",
    # need a screen, a video, the internet or a song
    "bad_apple", "ModernArt", "text", "windowDisplay", "BusTrack",
    # the night show has its own
    "Starry Night",
    # light pixels by number on the tree, or draw nothing on the house
    "Murica", "3d Renderer - Christmas Joy Show",
}

## starry night

STAR_DENSITY = 0.12
"""Fraction of pixels that are stars"""
STAR_LEVEL = (0.12, 0.55)
TWINKLE = 0.25
"""How much a star's brightness wavers, as a fraction of it"""
TWINKLE_PERIOD = (3.0, 10.0)
STAR_SWAPS_PER_MINUTE = 6
"""Now and then a star goes out and another comes on somewhere else"""
STAR_COLOURS = np.array([
    (1.00, 0.95, 0.80),  # warm white
    (1.00, 1.00, 1.00),
    (0.80, 0.88, 1.00),  # blue white
])
SHOOTING_EVERY = 7.0
"""Mean seconds between shooting stars on the fence"""
SHOOTING_SPEED = (5.0, 9.0)
"""Metres of fence per second"""
SHOOTING_LIFE = (0.8, 1.6)
SHOOTING_TRAIL = 0.86
"""How much of its brightness each pixel of a trail keeps each frame"""
NIGHT_GAMMA = 2.0

DIR = os.path.dirname(os.path.abspath(__file__))
TREE_MIN = np.array([-1.0, -1.0, 0.0])
TREE_MAX = np.array([1.0, 1.0, 4.0])

attach(FPS)

FIXTURES: dict[str, Fixture] = {"fence": fence_graph, "front": front_graph, "hedge": hedge_wall}


def mode_at(now: datetime.datetime) -> str:
    h = now.hour
    if RANDOM_FROM <= h < STARRY_FROM:
        return "random"
    if h >= STARRY_FROM or h < STARRY_UNTIL:
        return "starry"
    return "off"


def write(f: Fixture, rgb: np.ndarray):
    """Put a 0-255 float array on fixture f"""
    f._rgb[:] = np.clip(rgb, 0, 255).astype(np.uint8)
    f._changed_arr[:] = True
    f._lerp_total[:] = 0  # a fade() left by the last pattern would drag this to black


## random patterns

def tree_stand_in(f: Fixture) -> Volume:
    """A Volume with f's pixels squashed into the tree's box, each axis on its own"""
    p = f._positions.astype(np.float64)
    lo, hi = p.min(0), p.max(0)
    span = hi - lo
    mid = (TREE_MIN + TREE_MAX) / 2
    # flat fixtures get a hair of depth, patterns that divide by their bounding box's size crash otherwise
    hair = 0.02 * np.sin(np.arange(len(p)) * 2.4)[:, None]
    scaled = np.where(span > 1e-6, TREE_MIN + (p - lo) / np.where(span > 1e-6, span, 1) * (TREE_MAX - TREE_MIN), mid + hair)
    # flat fixtures sit on the trunk, not half way up it
    if span[2] <= 1e-6:
        scaled[:, 2] = np.abs(hair[:, 0])
    return Volume([tuple(map(float, c)) for c in scaled])


STAND_INS: dict[str, Volume] = {key: tree_stand_in(f) for key, f in FIXTURES.items()}


def candidates() -> list[str]:
    names = []
    for file in sorted(os.listdir(DIR)):
        if not file.endswith(".py") or file.startswith("_"):
            continue
        n = file[:-3]
        if n in EXCLUDE or n == __name__.rsplit(".", 1)[-1]:
            continue
        try:
            with open(os.path.join(DIR, file)) as fh:
                src = fh.read()
        except OSError:
            continue
        if "set_music(" in src:
            continue
        if "def draw_graph(" in src:
            names.append(n)  # graph patterns are displays, but only to connect the house
        elif "def draw(" in src and "def display_update" not in src:
            names.append(n)
    return names


broken: set[str] = set()
_loaded = 0


def load(pattern: str, on: Fixture):
    """Import a fresh copy of a pattern with fixture `on` active"""
    global _loaded
    _loaded += 1
    mod_name = f"_house_schedule_{_loaded}"
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(DIR, pattern + ".py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    real_attach = house_fixtures.attach
    house_fixtures.attach = lambda *a, **k: None  # graph patterns connect the house on import
    setActiveFixture(on)
    try:
        spec.loader.exec_module(module)
    finally:
        house_fixtures.attach = real_attach
        setActiveFixture(None)
        # graph patterns set the house's draw functions on import, ours go back below
        for key, f in FIXTURES.items():
            f.set_draw_fn(DRAW_FNS.get(key))
    return module, mod_name


class NoDrawFor(Exception):
    """The pattern only draws on graphs and this fixture isn't one"""


class Program:
    """One pattern's draw() running on one fixture of the house"""

    def __init__(self, pattern: str, key: str):
        self.pattern = pattern
        self.fixture = FIXTURES[key]
        self.mod_name: Optional[str] = None

        if isinstance(self.fixture, Graph) and self.has_graph_draw(pattern):
            module, self.mod_name = load(pattern, self.fixture)
            self.target: Optional[Volume] = None
            self.fn = module.draw_graph
        else:
            if not self.has_tree_draw(pattern):
                raise NoDrawFor(pattern)
            self.target = STAND_INS[key]
            reset_fixture(self.target)
            module, self.mod_name = load(pattern, self.target)
            fn = getattr(module, "draw", None)
            if fn is None:
                self.close()
                raise NoDrawFor(pattern)
            self.target.set_draw_fn(fn)
            self.fn = fn
        self.generator = None

    @staticmethod
    def has_graph_draw(pattern: str) -> bool:
        with open(os.path.join(DIR, pattern + ".py")) as fh:
            return "def draw_graph(" in fh.read()

    @staticmethod
    def has_tree_draw(pattern: str) -> bool:
        with open(os.path.join(DIR, pattern + ".py")) as fh:
            return "def draw(" in fh.read()

    def draw(self):
        f = self.fixture
        if self.target is not None:
            t = f._clock.frame_time or 0.0
            rgb = self.target._request_frame(t)
            setActiveFixture(f)
            write(f, rgb * RANDOM_BRIGHTNESS)
            return
        if self.generator is not None:
            try:
                next(self.generator)
                return
            except StopIteration:
                self.generator = None
        ret = self.fn()
        if hasattr(ret, "__next__"):
            self.generator = ret
            next(self.generator)

    def close(self):
        if self.mod_name is not None:
            sys.modules.pop(self.mod_name, None)


def reset_fixture(f: Fixture):
    f.set_draw_fn(None)
    f._rgb[:] = 0
    f._changed_arr[:] = False
    f._lerp_prev[:] = 0
    f._lerp_target[:] = 0
    f._lerp_step[:] = 0
    f._lerp_total[:] = 0
    f._shapes = []
    f._background = None


class RandomShow:
    def __init__(self):
        self.programs: dict[str, Program] = {}
        self.current: Optional[str] = None
        self.recent: list[str] = []
        self.next_switch = 0.0

    def stop(self):
        for p in self.programs.values():
            p.close()
        self.programs = {}
        self.current = None
        self.next_switch = 0.0

    def switch(self, now: float):
        self.stop()
        attribute.Store.get_store().reset()
        pool = [n for n in candidates() if n not in broken]
        fresh = [n for n in pool if n not in self.recent] or pool
        if not fresh:
            self.next_switch = now + SLOT_SECONDS
            return
        pattern = random.choice(fresh)
        try:
            for key in FIXTURES:
                try:
                    self.programs[key] = Program(pattern, key)
                except NoDrawFor:
                    # a graph pattern, the hedge gets a tree pattern to go with it
                    others = [n for n in pool if n != pattern and Program.has_tree_draw(n)]
                    if others:
                        self.programs[key] = Program(random.choice(others), key)
        except Exception:
            self.fail(pattern)
            return
        self.current = pattern
        self.recent = (self.recent + [pattern])[-min(NO_REPEAT, max(1, len(pool) - 1)):]
        self.next_switch = now + SLOT_SECONDS
        print(f"[house schedule] now showing {pattern}")

    def fail(self, pattern: str):
        print(f"[house schedule] {pattern} crashed, leaving it out")
        traceback.print_exc()
        broken.add(pattern)
        self.stop()  # next_switch is 0, so another is picked on the next tick

    def draw(self, key: str):
        f = get_active_fixture()
        program = self.programs.get(key)
        if program is None:
            write(f, np.zeros_like(f._rgb, dtype=np.float64))
            return
        try:
            program.draw()
        except Exception:
            self.fail(program.pattern)
            setActiveFixture(f)
            write(f, np.zeros_like(f._rgb, dtype=np.float64))


## starry night

class Sky:
    """Still stars on one fixture"""

    def __init__(self, f: Fixture):
        self.n = f._num_pixels
        self.level = np.zeros(self.n)
        self.colour = np.zeros((self.n, 3))
        self.period = np.ones(self.n)
        self.phase = np.zeros(self.n)
        for i in np.nonzero(np.random.random(self.n) < STAR_DENSITY)[0]:
            self.light(i)

    def light(self, i: int):
        self.level[i] = random.uniform(*STAR_LEVEL)
        self.colour[i] = STAR_COLOURS[random.randrange(len(STAR_COLOURS))]
        self.period[i] = random.uniform(*TWINKLE_PERIOD)
        self.phase[i] = random.uniform(0, 2 * math.pi)

    def brightness(self, t: float, dt: float) -> np.ndarray:
        if random.random() < STAR_SWAPS_PER_MINUTE / 60 * dt:
            lit = np.nonzero(self.level)[0]
            if len(lit):
                self.level[random.choice(lit)] = 0
            dark = np.nonzero(self.level == 0)[0]
            if len(dark):
                self.light(int(random.choice(dark)))
        wave = np.sin(2 * math.pi * t / self.period + self.phase)
        return self.level * (1 + TWINKLE * wave)


class ShootingStar:
    def __init__(self, g: Graph):
        self.edge = random.choice([e for e in g.edges() if len(e)])
        self.start = random.choice(self.edge.vertices)
        self.s = random.uniform(0, self.edge.length)
        self.speed = random.uniform(*SHOOTING_SPEED)
        self.life = random.uniform(*SHOOTING_LIFE)
        self.age = 0.0
        self.colour = STAR_COLOURS[random.randrange(len(STAR_COLOURS))]

    def step(self, dt: float) -> Optional[int]:
        """Move on, returning the index of the pixel it's on, None once it's gone"""
        self.age += dt
        if self.age >= self.life:
            return None
        self.s += self.speed * dt
        while self.s >= self.edge.length:
            self.s -= self.edge.length
            at = self.edge.other(self.start)
            ways = self.edge.edges_at(at)
            if not ways:
                return None  # the end of the fence
            self.edge, self.start = random.choice(ways), at
        p = self.edge.pixel_at(self.s / self.edge.length if self.edge.length else 0, self.start)
        return None if p is None else p._id

    def glow(self) -> float:
        """Fades in quickly and out slowly"""
        x = self.age / self.life
        return min(1.0, x / 0.15) * (1 - x) ** 0.5


class NightShow:
    def __init__(self):
        self.skies = {key: Sky(f) for key, f in FIXTURES.items()}
        self.trail = np.zeros((fence_graph._num_pixels, 3))
        self.shooting: list[ShootingStar] = []
        self.last: dict[str, float] = {}

    def draw(self, key: str):
        f = get_active_fixture()
        t = f._clock.frame_time or 0.0
        dt = min(max(t - self.last.get(key, t), 0.0), 0.1)
        self.last[key] = t

        sky = self.skies[key]
        light = sky.brightness(t, dt)[:, None] * sky.colour

        if key == "fence":
            self.trail *= SHOOTING_TRAIL ** (dt * FPS)
            if random.random() < dt / SHOOTING_EVERY:
                self.shooting.append(ShootingStar(fence_graph))
            alive = []
            for s in self.shooting:
                i = s.step(dt)
                if i is None:
                    continue
                self.trail[i] = np.maximum(self.trail[i], s.glow() * s.colour)
                alive.append(s)
            self.shooting = alive
            light = np.maximum(light, self.trail)

        write(f, 255 * np.clip(light, 0, 1) ** NIGHT_GAMMA)


## running it

random_show = RandomShow()
night_show: Optional[NightShow] = None
mode = ""


def make_draw(key: str) -> Callable[[], None]:
    def draw():
        if mode == "random":
            random_show.draw(key)
        elif mode == "starry" and night_show is not None:
            night_show.draw(key)
        else:
            f = get_active_fixture()
            write(f, np.zeros_like(f._rgb, dtype=np.float64))
    return draw


DRAW_FNS = {key: make_draw(key) for key in FIXTURES}
for key, f in FIXTURES.items():
    f.set_draw_fn(DRAW_FNS[key])


def display_update():
    global mode, night_show
    now = datetime.datetime.now()
    m = mode_at(now)
    if m != mode:
        print(f"[house schedule] {now:%H:%M} switching to {m}")
        if mode == "random":
            random_show.stop()
        night_show = NightShow() if m == "starry" else None
        mode = m
    if mode == "random" and now.timestamp() >= random_show.next_switch:
        random_show.switch(now.timestamp())
