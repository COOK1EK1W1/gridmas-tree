"""Harder Better Faster Stronger on the house: the hedge, the fence and the front.

The song is 123.48 bpm, so at 41.16 fps every beat is exactly 20 frames, and beat 0 is FIRST_BEAT into the mp3. display_update()
picks which section of the song is playing and puts that section's draw() on every
fixture; each draw() then only has to think in beats and frames since its own section
started. Every fixture runs the same draw(), a group of pixels knows which of its pixels
are on each fixture, so a "quadrant" is a pie slice of the hedge, a run of the fence and
a square on the front.

How bright the show is at each point in the song is set by BRIGHTNESS, not the sections.
"""

import math
import random
from typing import NamedTuple, Optional

import numpy as np

from pixel_driver import DISPLAY_TICK_FPS
from fixture import Fixture, get_active_fixture, setActiveFixture
from house_fixtures import attach, fence_graph, front_graph, hedge_wall
from gridmas import *

name = "Harder Better Faster Stronger (House)"
author = "Ciaran"

# not in git, put the song next to this file
set_music("harderstronger.mp3")

FPS = 41.1602
BEAT = 20
BAR = 4 * BEAT
FIRST_BEAT = 0.211
"""Seconds into the mp3 of beat 0, from tools/song/song.py summary"""


## where a pixel sits on its fixture

class Spot(NamedTuple):
    rise: float
    """How far up (0-1)"""
    turn: Optional[float]
    """How far round (0-1), None to stay out of the quadrants and octants"""
    left: bool
    stripe: float
    """Where the rainbow stripes put it, they wrap every 1"""
    along: float
    """How far along the fixture (0-1), for things that run down its length"""


HEDGE_ASPECT = 16 / 9

def hedge_place(i: int, pixel: Pixel) -> Spot:
    """The hedge is a flat wall scanned onto -1 to 1 by 0 to height(), "round" spins about its middle"""
    across = (pixel.x + 1) / 2
    rise = pixel.z / height()
    turn = (math.atan2(rise - 0.5, (across - 0.5) * HEDGE_ASPECT) + math.pi) / (2 * math.pi)
    return Spot(rise, turn, pixel.x < 0, rise + (0.5 if pixel.x > 0 else 1), across)


def along_paths(graph: Graph, paths: list[list[int]]) -> dict[int, tuple[int, float]]:
    """Each pixel on one of the paths of vertex ids: (which path, how far along it by distance, 0-1).
    A pixel at a vertex where one path ends and the next starts goes with the next"""
    found: dict[int, tuple[int, float]] = {}
    ends: list[tuple[int, int]] = []
    for n, path in enumerate(paths):
        vs = [graph.vertices(v) for v in path]
        steps = [next(e for e in a.edges if e.other(a) is b) for a, b in zip(vs, vs[1:])]
        total = sum(e.length for e in steps)
        done = 0.0
        for a, edge in zip(vs, steps):
            for pixel in a.pixels:
                found.setdefault(pixel.id, (n, done / total))
            for pixel, t in zip(edge.pixels_from(a), edge.t_from(a)):
                found.setdefault(pixel.id, (n, (done + t * edge.length) / total))
            done += edge.length
        ends += [(n, pixel.id) for pixel in vs[-1].pixels]
    for n, i in ends:
        found.setdefault(i, (n, 1.0))
    return found


FENCE_RUNS = along_paths(fence_graph, [[0, 1], [1, 2, 3, 4, 5], [5, 6], [6, 7]])
"""Vertex ids (A-H in house-fence.txt): the short side, the gate, then the two long sides"""

def fence_place(i: int, pixel: Pixel) -> Spot:
    """The fence is one long line, so "up" is along it and "round" is each run in turn"""
    along = i / num_pixels()
    run, through = FENCE_RUNS.get(i, (0, along))
    return Spot(along, (run + through) / 4, along < 0.5, along * 3 % 1 + along, along)


FRONT_SQUARES = along_paths(front_graph, [[0, 1, 2, 3, 0], [4, 5, 6, 7, 4], [8, 9, 10, 11, 8], [12, 13, 14, 15]])
"""Vertex ids (A-P in house-front.txt): the door, the window beside it, then the two upstairs
(the last one is open, its fourth side is the wire up from the door). The wires between them aren't in a square"""

def front_place(i: int, pixel: Pixel) -> Spot:
    """The front is four squares on a wall, "round" goes round each square in turn"""
    rise = pixel.z / height()
    left = pixel.x < -2.8
    along = i / num_pixels()
    if i in FRONT_SQUARES:
        square, round_square = FRONT_SQUARES[i]
        return Spot(rise, (square + round_square) / 4, left, round_square + rise, along)
    return Spot(rise, None, left, along + rise, along)


PLACES = {hedge_wall: hedge_place, fence_graph: fence_place, front_graph: front_place}

attach(FPS)


## groups of pixels the sections light up

NUM_LAYERS = 16

class Group:
    """Some pixels on each fixture, added together like lists"""

    def __init__(self, on: Optional[dict[Fixture, list[Pixel]]] = None):
        self.on = on or {fixture: [] for fixture in PLACES}

    def __add__(self, other: "Group") -> "Group":
        return Group({fixture: self.on[fixture] + other.on[fixture] for fixture in PLACES})


LAYERS = [Group() for _ in range(NUM_LAYERS)]
"""Horizontal slices of each fixture, bottom to top"""
QUADRANTS = [Group() for _ in range(4)]
"""A pie slice of the hedge, a run of the fence, a square of the front"""
OCTANTS = [Group() for _ in range(8)]
"""Half of each quadrant"""
NUM_HELIX = 24
HELIX = [Group() for _ in range(NUM_HELIX)]
"""Rainbow stripes"""
NUM_SWEEP = 32
SWEEP = [Group() for _ in range(NUM_SWEEP)]
"""Slices down the length of each fixture"""
LEFT = Group()
RIGHT = Group()

for fixture, place in PLACES.items():
    setActiveFixture(fixture)
    for i, pixel in enumerate(pixels()):
        spot = place(i, pixel)
        layer = min(NUM_LAYERS - 1, int(spot.rise * NUM_LAYERS))
        LAYERS[layer].on[fixture].append(pixel)
        if spot.turn is not None:
            QUADRANTS[int(spot.turn * 4) % 4].on[fixture].append(pixel)
            OCTANTS[int(spot.turn * 8) % 8].on[fixture].append(pixel)
        HELIX[int(spot.stripe * NUM_HELIX) % NUM_HELIX].on[fixture].append(pixel)
        SWEEP[min(NUM_SWEEP - 1, int(spot.along * NUM_SWEEP))].on[fixture].append(pixel)
        (LEFT if spot.left else RIGHT).on[fixture].append(pixel)

setActiveFixture(None)

EVERYTHING = sum(LAYERS, Group())
BANDS = [sum(LAYERS[i:i + 4], Group()) for i in range(0, NUM_LAYERS, 4)]
"""Four thick slices, bottom to top"""
SLICES = [LAYERS[i] + LAYERS[i + 1] for i in range(0, NUM_LAYERS, 2)]
"""Eight slices, bottom to top"""
TOP_HALF = BANDS[2] + BANDS[3]


LEVEL = 1.0
"""How bright the show is right now, display_update() follows BRIGHTNESS"""

def dim(color: Color, brightness: float) -> Color:
    return Color.mix(Color.black(), color, brightness)


def light(group: Group, color: Color):
    color = dim(color, LEVEL)
    for pixel in group.on[get_active_fixture()]:
        pixel.set_color(color)


def flood(color: Color):
    fill(dim(color, LEVEL))


def sparkle(group: Group, count: int, color: Color):
    """Light random pixels of the group, count is per 1000 pixels of the fixture so a busy bar doesn't strobe"""
    fixture = get_active_fixture()
    here = group.on[fixture]
    share = round(count * fixture._num_pixels / 1000)
    color = dim(color, LEVEL)
    for pixel in random.sample(here, min(share, len(here))):
        pixel.set_color(color)


## intro

def silence():
    fill(Color.black())


def highpass():
    """8 bars of muffled intro: a blue pulse on each beat that climbs and brightens as the filter opens"""
    lerp(Color.black(), 16)
    beat, f = divmod(frame(), BEAT)
    if f == 0:
        progress = beat / 32
        top = 2 + int(progress * (NUM_LAYERS - 2))
        color = dim(Color.mix(Color.blue(), Color.cyan(), progress), 0.25 + 0.5 * progress)
        for layer in LAYERS[:top]:
            light(layer, color)


def highs():
    """8 bars of high instruments: a quarter of the house chases round on the beat, sparkles on the hats"""
    lerp(Color.black(), 9)
    beat, f = divmod(frame(), BEAT)
    bar = beat // 4

    if f == 0:
        # reverse the chase every two bars
        step = beat % 4 if (bar // 2) % 2 == 0 else 3 - beat % 4
        light(QUADRANTS[step], dim(Color.fuchsia() if bar % 2 == 0 else Color.violet(), 0.6))

    if f == 10:
        sparkle(EVERYTHING, 120, Color.white())
    elif f % 5 == 0:
        sparkle(EVERYTHING, 30, Color.cyan())


KICKS = [Color.red(), Color.orange(), Color.fuchsia(), Color.amber()]

def bass():
    """8 bars with the bass in: the whole house kicks on the beat, then fills up white into the first lyric"""
    beat, f = divmod(frame(), BEAT)
    bar = beat // 4

    if bar == 7:
        lerp(Color.black(), 6)
        filled = int(frame() % BAR / BAR * NUM_LAYERS) + 1
        for layer in LAYERS[:filled]:
            light(layer, Color.white())
        return

    lerp(Color.black(), 14)
    if f == 0:
        flood(KICKS[bar % len(KICKS)])
    if f == 10:
        sparkle(TOP_HALF, 150, Color.white())


## lyrics, every line is 4 bars: 4 words of 2 beats each, then 2 bars of instrumental

WORD = 2 * BEAT

def instrumental(beat: int, f: int, color: Color, accent: Color):
    """A pulse on each beat with a white band sweeping up the house for a bar, then back down"""
    if f == 0:
        flood(dim(color if beat % 2 == 0 else accent, 0.5))

    position = (beat * BEAT + f) % BAR / BAR
    if beat >= 4:
        position = 1 - position
    light(LAYERS[min(NUM_LAYERS - 1, int(position * NUM_LAYERS))], Color.white())


def lyric_line(words: list[Group], color: Color, accent: Color, build: bool, finale: bool = False):
    """Make the draw() for one line of lyrics

    Args:
        words: The part of the house each of the 4 words lights up
        color: The color of the words
        accent: Second color used in the instrumental
        build: Keep earlier words dimly lit so the house fills up over the line
        finale: Flash the whole house on the last word
    """
    def draw():
        lerp(Color.black(), 12)
        word, f = divmod(frame(), WORD)

        if word >= 4:
            beat, f = divmod(frame() - 4 * WORD, BEAT)
            instrumental(beat, f, color, accent)
            return

        if build:
            for earlier in words[:word]:
                light(earlier, dim(color, 0.3))
        # every word hits white then holds its color, with a nudge on its second beat
        if f < 3:
            light(words[word], Color.white())
        elif BEAT <= f < BEAT + 3:
            light(words[word], accent)
        else:
            light(words[word], color)
        if finale and word == 3 and f < 3:
            flood(Color.white())

    return draw


## fast verses: a syllable on every quaver, so a line is one bar and a verse is four
#
#   Work it harder, make it better
#   Do it faster, makes us stronger
#   More than ever, hour after
#   Hour, work is never over
#
# A section is built out of bars. Each bar is a function of the frame within that bar,
# usually a sung line (one of 8 parts of the house per syllable) over some backing layers.

QUAVER = BEAT // 2
RAINBOW = [Color.hsl(i / 8, 1, 1) for i in range(8)]


def bars(*bar_fns, fade: int = 12):
    """Make a draw() that plays one bar function after another"""
    def draw():
        lerp(Color.black(), fade)
        bar, f = divmod(frame(), BAR)
        if bar < len(bar_fns):
            bar_fns[bar](f)
    return draw


# backing layers

def kick(color: Color, level: float = 0.5):
    """The whole house pulses on every beat"""
    def layer(f: int):
        if f % BEAT == 0:
            flood(dim(color, level))
    return layer


def thump(color: Color):
    """Just the bottom of the house on every beat, for when it's only drums"""
    def layer(f: int):
        if f % BEAT == 0:
            light(BANDS[0], color)
    return layer


def hats(count: int, color: Color = Color.white()):
    """Sparkles in the top of the house between the beats"""
    def layer(f: int):
        if f % BEAT == QUAVER:
            sparkle(TOP_HALF, count, color)
    return layer


def comet(color: Color):
    """A light that runs the whole length of every fixture each bar, the fading leaves its tail"""
    def layer(f: int):
        light(SWEEP[f * NUM_SWEEP // BAR], color)
    return layer


# bars

def sung(segments: list[Group], colors: list[Color], *backing,
         build: bool = True, hit: Color = Color.white(), vocals_only_from: int = BAR):
    """A bar with a line sung over it

    Args:
        segments: 8 parts of the house, one lit per syllable
        colors: The color of each syllable, repeated if there are fewer than 8
        backing: Layers drawn underneath
        build: Keep earlier syllables dimly lit so the house fills up over the line
        hit: What each syllable flashes as it lands
        vocals_only_from: Frame of the bar where the backing cuts out and leaves the voice alone
    """
    def bar(f: int):
        q, qf = divmod(f, QUAVER)
        if f >= vocals_only_from:
            # nothing but the voice: one stark hit per syllable on a dark house
            if qf < 6:
                light(segments[q], Color.white())
            return

        for layer in backing:
            layer(f)
        if build:
            for i in range(q):
                light(segments[i], dim(colors[i % len(colors)], 0.3))
        light(segments[q], hit if qf < 3 else colors[q % len(colors)])
    return bar


def break_bar(color: Color, accent: Color, down: bool = False):
    """A bar of instrumental between lines, the white band sweeps up (or back down)"""
    def bar(f: int):
        instrumental(f // BEAT + (4 if down else 0), f % BEAT, color, accent)
    return bar


def descending(color: Color, *backing):
    """A sung bar where the voice drops an octave each beat, so the light steps down the house"""
    def bar(f: int):
        beat, bf = divmod(f, BEAT)
        for layer in backing:
            layer(f)
        for higher in range(beat):
            light(BANDS[3 - higher], dim(color, 0.25))
        light(BANDS[3 - beat], Color.white() if bf % QUAVER < 3 else color)
    return bar


def half_sung(color: Color, accent: Color):
    """Half a line in the first two beats, then two beats of instrumental"""
    def bar(f: int):
        if f < 2 * BEAT:
            q, qf = divmod(f, QUAVER)
            for i in range(q):
                light(QUADRANTS[i], dim(color, 0.3))
            light(QUADRANTS[q], Color.white() if qf < 3 else color)
            return
        f -= 2 * BEAT
        if f % BEAT == 0:
            flood(dim(accent, 0.5))
        light(LAYERS[min(NUM_LAYERS - 1, int(f / (2 * BEAT) * NUM_LAYERS))], Color.white())
    return bar


def low_ending(color: Color, *backing):
    """The very last line: "never over" drops right down in pitch, and the light sinks to the floor"""
    line = sung(SLICES, [color], *backing)
    def bar(f: int):
        if f < 2 * BEAT:
            line(f)
            return
        step = (f - 2 * BEAT) // QUAVER
        light(BANDS[3 - step], dim(Color.red(), 1 - 0.2 * step))
    return bar


def verse(colors: list[list[Color]], *backing, flip: bool = False, **kwargs):
    """The four sung bars of a verse, the lines climb, fall, then spin one way and back

    Args:
        colors: The syllable colors for each of the 4 lines
        backing: Layers drawn underneath every line
        flip: Spin first, then climb and fall
    """
    segments = [SLICES, SLICES[::-1], OCTANTS, OCTANTS[::-1]]
    if flip:
        segments = segments[2:] + segments[:2]
    return [sung(segments[i], colors[i], *backing, **kwargs) for i in range(4)]


def helix():
    """4 bars of instrumental: a rainbow spirals up the house and flashes on the beat"""
    lerp(Color.black(), 8)
    shift = frame() // 2
    for i, stripe in enumerate(HELIX):
        light(stripe, HELIX_COLORS[(i - shift) % NUM_HELIX])
    if frame() % BEAT < 3:
        flood(Color.white())

HELIX_COLORS = [Color.hsl(i / NUM_HELIX, 1, 1) for i in range(NUM_HELIX)]


# two lines, two bars of instrumental, twice
verse_with_breaks = bars(
    sung(SLICES, [Color.red()], kick(Color.red(), 0.25)),
    sung(SLICES[::-1], [Color.orange()], kick(Color.orange(), 0.25)),
    break_bar(Color.red(), Color.orange()),
    break_bar(Color.red(), Color.orange(), down=True),
    sung(OCTANTS, [Color.cyan()], kick(Color.blue(), 0.25)),
    sung(OCTANTS[::-1], [Color.sky()], kick(Color.blue(), 0.25)),
    break_bar(Color.cyan(), Color.blue()),
    break_bar(Color.cyan(), Color.blue(), down=True),
)

# the first verse sung straight through
verse_straight = bars(*verse(
    [[Color.amber()], [Color.yellow()], [Color.fuchsia()], [Color.violet()]],
    kick(Color.red(), 0.4), hats(80), comet(Color.white()),
))

# the backing drops to drums: dim, sparse, cold. Then it builds verse by verse
drums_only = bars(
    *verse([[dim(Color.blue(), 0.5)]] * 4, build=False, hit=dim(Color.white(), 0.6)),
    *verse([[dim(Color.sky(), 0.6)]] * 4, thump(dim(Color.white(), 0.5)), build=False, hit=dim(Color.white(), 0.8)),
    fade=8,
)

build_up = bars(
    *verse([[Color.teal()]] * 4, thump(Color.white()), hats(40), comet(Color.teal()), flip=True)[:3],
    # vocals only on "never over"
    sung(OCTANTS[::-1], [Color.teal()], thump(Color.white()), hats(40), comet(Color.teal()), vocals_only_from=2 * BEAT),
)

# the voice turns synthy, so the syllables go rainbow
synth_build = bars(
    *verse([RAINBOW] * 4, kick(Color.indigo(), 0.3), thump(Color.white()), hats(80)),
    *verse([RAINBOW[::-1]] * 4, kick(Color.violet(), 0.5), hats(150), flip=True)[:3],
    # vocals only on "never over"
    sung(SLICES[::-1], RAINBOW, kick(Color.violet(), 0.5), hats(150), vocals_only_from=2 * BEAT),
)

OCTAVE_COLORS = [Color.lime(), Color.emerald(), Color.cyan(), Color.sky()]
descending_octaves = bars(*[
    descending(OCTAVE_COLORS[i % 4], kick(OCTAVE_COLORS[(i + 2) % 4], 0.3), hats(60), comet(Color.white()))
    for i in range(8)
])

# everything at once
full_tilt = bars(
    *verse([RAINBOW] * 4, kick(Color.red(), 0.6), hats(150), flip=True),
    *verse([[Color.white()]] * 4, kick(Color.fuchsia(), 0.6), hats(150), hit=Color.yellow()),
    *verse([RAINBOW[::-1]] * 4, kick(Color.cyan(), 0.6), hats(150)),
)

half_lines = bars(
    half_sung(Color.orange(), Color.red()),
    half_sung(Color.amber(), Color.orange()),
    half_sung(Color.yellow(), Color.amber()),
    sung(OCTANTS, RAINBOW, kick(Color.red(), 0.5)),
)

last_verse = bars(
    *verse([[Color.rose()], [Color.red()], [Color.orange()], [Color.red()]], kick(Color.red(), 0.4), hats(100))[:3],
    low_ending(Color.red(), kick(Color.red(), 0.4)),
    fade=14,
)


def outro():
    lerp(Color.black(), 40)


# (first beat, draw function), in song order
SECTIONS = [
    (0, silence),
    (10, highpass),
    (42, highs),
    (74, bass),
    # Work it, make it, do it, makes us
    (106, lyric_line(QUADRANTS, Color.red(), Color.orange(), build=True)),
    # Harder, better, faster, stronger
    (122, lyric_line(BANDS, Color.amber(), Color.yellow(), build=True, finale=True)),
    # More than, hour, hour, never
    (138, lyric_line([LEFT, RIGHT, LEFT, RIGHT], Color.cyan(), Color.blue(), build=False)),
    # Ever, after, work is, over
    (154, lyric_line(BANDS[::-1], Color.violet(), Color.fuchsia(), build=True)),
    # Work it, make it, do it, makes us
    (170, lyric_line(QUADRANTS[::-1], Color.lime(), Color.emerald(), build=True)),
    # Harder, better, faster, stronger
    (186, lyric_line(BANDS, Color.rose(), Color.red(), build=True, finale=True)),
    # from here a syllable on every quaver, a line per bar
    (202, verse_with_breaks),   # 8 bars
    (234, verse_straight),      # 4 bars
    (250, drums_only),          # 8 bars
    (282, build_up),            # 4 bars
    (298, synth_build),         # 8 bars
    (330, helix),               # 4 bars instrumental
    (346, descending_octaves),  # 8 bars
    (378, full_tilt),           # 12 bars
    (426, half_lines),          # 4 bars
    (442, last_verse),          # 4 bars
    (458, outro),
]


# (beat, brightness) through the song, it slides between points and a jump is two points side by side.
# 1 is full, reserved for the peaks. The bottom of the range is about a third because the
# drivers send 4 bit color, anything lower runs out of steps to fade through.
BRIGHTNESS = [
    (0, 1),
    (41.99, 1),         # the muffled intro is dark by itself
    (42, 0.35),
    (101.99, 0.35),
    (106, 0.7),         # the white fill into the first lyric
    (106.01, 0.4),
    (122, 0.4),
    (138, 0.65),        # harder, better, faster, stronger
    (138.01, 0.4),
    (186, 0.45),
    (201.99, 0.85),     # and again, bigger
    (202, 0.4),
    (234, 0.4),
    (249.99, 0.55),
    (250, 1),           # drums only is dark by itself
    (281.99, 1),
    (282, 0.35),
    (297.99, 0.6),
    (298, 0.5),
    (329.99, 1),        # the voice goes synthy and climbs into the rainbows
    (345.99, 1),
    (346, 0.4),
    (377.99, 0.6),
    (378, 0.5),
    (425.99, 1),        # everything at once, the top of the show
    (426, 0.5),
    (442, 0.5),
    (458, 0.35),
]
BEATS, LEVELS = zip(*BRIGHTNESS)


def display_update():
    global LEVEL
    # this ticks at 45Hz while the fixtures draw at 41fps, so look one tick ahead:
    # a section goes on them just before the frame its first beat lands on
    beat = ((frame() + 1) / DISPLAY_TICK_FPS - FIRST_BEAT) * FPS / BEAT
    LEVEL = float(np.interp(beat, BEATS, LEVELS))
    current = silence
    for first_beat, draw in SECTIONS:
        if first_beat <= beat:
            current = draw
    for fixture in PLACES:
        fixture.set_draw_fn(current)
