"""Harder Better Faster Stronger, a display choreographed to the song.

The song is 123 bpm, so at 41 fps every beat is exactly 20 frames. display_update()
picks which section of the song is playing and puts that section's draw() on the tree;
each draw() then only has to think in beats and frames since its own section started.
"""

import math
import random

from pixel_driver import DISPLAY_TICK_FPS, driver_registry
from fixture import Volume, setActiveFixture
from gridmas import *

name = "Harder Better Faster Stronger"
author = "Ciaran"

# not in git, put the song next to this file
set_music("harderstronger.mp3")

FPS = 41.15
BEAT = 20
BAR = 4 * BEAT

tree = Volume.from_csv("tree.csv")
try:
    from network_driver import NetworkPixelDriver
    driver = NetworkPixelDriver("gridmastree.local", tree._num_pixels, "tree")
except ImportError:
    # the web editor's pyodide runtime has no requests, the browser pulls frames instead
    from web_driver import WebPixelDriver
    driver = WebPixelDriver(tree._num_pixels, "tree")
driver.add_fixture(tree, 0)
driver_registry.register(driver)


## groups of pixels the sections light up

NUM_LAYERS = 16

setActiveFixture(tree)
set_fps(FPS)

LAYERS: list[list[Pixel]] = [[] for _ in range(NUM_LAYERS)]
"""Horizontal slices of the tree, bottom to top"""
QUADRANTS: list[list[Pixel]] = [[] for _ in range(4)]
"""Quarters of the tree going round the trunk"""
OCTANTS: list[list[Pixel]] = [[] for _ in range(8)]
"""Eighths of the tree going round the trunk"""
NUM_HELIX = 24
HELIX: list[list[Pixel]] = [[] for _ in range(NUM_HELIX)]
"""Stripes that spiral up the tree"""
LEFT: list[Pixel] = []
RIGHT: list[Pixel] = []

for pixel in pixels():
    layer = min(NUM_LAYERS - 1, int(pixel.z / height() * NUM_LAYERS))
    LAYERS[layer].append(pixel)
    turn = (pixel.a + math.pi) / (2 * math.pi)
    QUADRANTS[int(turn * 4) % 4].append(pixel)
    OCTANTS[int(turn * 8) % 8].append(pixel)
    HELIX[int((turn + pixel.z / height()) * NUM_HELIX) % NUM_HELIX].append(pixel)
    (LEFT if pixel.x < 0 else RIGHT).append(pixel)

setActiveFixture(None)

BANDS = [sum(LAYERS[i:i + 4], []) for i in range(0, NUM_LAYERS, 4)]
"""The tree in four thick slices, bottom to top"""
SLICES = [LAYERS[i] + LAYERS[i + 1] for i in range(0, NUM_LAYERS, 2)]
"""The tree in eight slices, bottom to top"""
TOP_HALF = BANDS[2] + BANDS[3]


def light(group: list[Pixel], color: Color):
    for pixel in group:
        pixel.set_color(color)


def dim(color: Color, brightness: float) -> Color:
    return Color.mix(Color.black(), color, brightness)


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
    """8 bars of high instruments: a quarter of the tree chases round on the beat, sparkles on the hats"""
    lerp(Color.black(), 9)
    beat, f = divmod(frame(), BEAT)
    bar = beat // 4

    if f == 0:
        # reverse the chase every two bars
        step = beat % 4 if (bar // 2) % 2 == 0 else 3 - beat % 4
        light(QUADRANTS[step], dim(Color.fuchsia() if bar % 2 == 0 else Color.violet(), 0.6))

    if f == 10:
        light(random.sample(pixels(), 120), Color.white())
    elif f % 5 == 0:
        light(random.sample(pixels(), 30), Color.cyan())


KICKS = [Color.red(), Color.orange(), Color.fuchsia(), Color.amber()]

def bass():
    """8 bars with the bass in: the whole tree kicks on the beat, then fills up white into the first lyric"""
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
        fill(KICKS[bar % len(KICKS)])
    if f == 10:
        light(random.sample(TOP_HALF, 150), Color.white())


## lyrics, every line is 4 bars: 4 words of 2 beats each, then 2 bars of instrumental

WORD = 2 * BEAT

def instrumental(beat: int, f: int, color: Color, accent: Color):
    """A pulse on each beat with a white band sweeping up the tree for a bar, then back down"""
    if f == 0:
        fill(dim(color if beat % 2 == 0 else accent, 0.5))

    position = (beat * BEAT + f) % BAR / BAR
    if beat >= 4:
        position = 1 - position
    light(LAYERS[min(NUM_LAYERS - 1, int(position * NUM_LAYERS))], Color.white())


def lyric_line(words: list[list[Pixel]], color: Color, accent: Color, build: bool, finale: bool = False):
    """Make the draw() for one line of lyrics

    Args:
        words: The part of the tree each of the 4 words lights up
        color: The color of the words
        accent: Second color used in the instrumental
        build: Keep earlier words dimly lit so the tree fills up over the line
        finale: Flash the whole tree on the last word
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
            fill(Color.white())

    return draw


## fast verses: a syllable on every quaver, so a line is one bar and a verse is four
#
#   Work it harder, make it better
#   Do it faster, makes us stronger
#   More than ever, hour after
#   Hour, work is never over
#
# A section is built out of bars. Each bar is a function of the frame within that bar,
# usually a sung line (one of 8 parts of the tree per syllable) over some backing layers.

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
    """The whole tree pulses on every beat"""
    def layer(f: int):
        if f % BEAT == 0:
            fill(dim(color, level))
    return layer


def thump(color: Color):
    """Just the bottom of the tree on every beat, for when it's only drums"""
    def layer(f: int):
        if f % BEAT == 0:
            light(BANDS[0], color)
    return layer


def hats(count: int, color: Color = Color.white()):
    """Sparkles in the top of the tree between the beats"""
    def layer(f: int):
        if f % BEAT == QUAVER:
            light(random.sample(TOP_HALF, count), color)
    return layer


# bars

def sung(segments: list[list[Pixel]], colors: list[Color], *backing,
         build: bool = True, hit: Color = Color.white(), vocals_only_from: int = BAR):
    """A bar with a line sung over it

    Args:
        segments: 8 parts of the tree, one lit per syllable
        colors: The color of each syllable, repeated if there are fewer than 8
        backing: Layers drawn underneath
        build: Keep earlier syllables dimly lit so the tree fills up over the line
        hit: What each syllable flashes as it lands
        vocals_only_from: Frame of the bar where the backing cuts out and leaves the voice alone
    """
    def bar(f: int):
        q, qf = divmod(f, QUAVER)
        if f >= vocals_only_from:
            # nothing but the voice: one stark hit per syllable on a dark tree
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
    """A sung bar where the voice drops an octave each beat, so the light steps down the tree"""
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
            fill(dim(accent, 0.5))
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
    """4 bars of instrumental: a rainbow spirals up the tree and flashes on the beat"""
    lerp(Color.black(), 8)
    shift = frame() // 2
    for i, stripe in enumerate(HELIX):
        light(stripe, HELIX_COLORS[(i - shift) % NUM_HELIX])
    if frame() % BEAT < 3:
        fill(Color.white())

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
    kick(Color.red(), 0.4), hats(80),
))

# the backing drops to drums: dim, sparse, cold. Then it builds verse by verse
drums_only = bars(
    *verse([[dim(Color.blue(), 0.5)]] * 4, build=False, hit=dim(Color.white(), 0.6)),
    *verse([[dim(Color.sky(), 0.6)]] * 4, thump(dim(Color.white(), 0.5)), build=False, hit=dim(Color.white(), 0.8)),
    fade=8,
)

build_up = bars(
    *verse([[Color.teal()]] * 4, thump(Color.white()), hats(40), flip=True)[:3],
    # vocals only on "never over"
    sung(OCTANTS[::-1], [Color.teal()], thump(Color.white()), hats(40), vocals_only_from=2 * BEAT),
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
    descending(OCTAVE_COLORS[i % 4], kick(OCTAVE_COLORS[(i + 2) % 4], 0.3), hats(60))
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


def display_update():
    # this ticks at 45Hz while the tree draws at 41fps, so look one tick ahead:
    # a section goes on the tree just before the frame its first beat lands on
    current = silence
    for first_beat, draw in SECTIONS:
        if first_beat * BEAT * DISPLAY_TICK_FPS <= (frame() + 1) * FPS:
            current = draw
    tree.set_draw_fn(current)
