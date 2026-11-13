from gridmas import *
from random import random, uniform, randint

# ---------------------------------------------------------------------------
# Firework pattern - first 200 LEDs only, linear index
#
# Physics-based: rockets launch with an initial velocity and decelerate
# under gravity until they reach apex and explode into sparks, which then
# fall under their own gravity + drag, fading as they go.
#
# Colour blending is done manually in a small float buffer so overlapping
# particles genuinely mix colours, rather than just overwriting each other.
# ---------------------------------------------------------------------------

NUM_LEDS = 250          # only drive the first 200 lights

DECAY = 0.80             # per-frame buffer fade (afterglow / motion blur)
LAUNCH_CHANCE = 0.025     # chance per frame of a new rocket launching
MAX_ROCKETS = 1

ROCKET_GRAVITY = -0.045   # deceleration on the way up
ROCKET_MIN_VEL = 3.0
ROCKET_MAX_VEL = 4.7

SPARK_GRAVITY = 0
SPARK_DRAG = 0.96
SPARK_MIN_SPEED = -3.4
SPARK_MAX_SPEED = 3.4
SPARK_COUNT_RANGE = (18, 28)
SPARK_LIFE_RANGE = (35, 65)


def hsl_to_rgb(h, s, l):
    """Standard HSL -> RGB (0-255 floats), needed since we blend raw RGB."""
    if s == 0:
        r = g = b = l
    else:
        def hue2rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue2rgb(p, q, h + 1/3)
        g = hue2rgb(p, q, h)
        b = hue2rgb(p, q, h - 1/3)
    return (r * 255, g * 255, b * 255)


def splat(buffer, pos, rgb, amount):
    """Add colour into the buffer at a fractional position, split across
    the two nearest pixels so motion looks smooth rather than stepping."""
    base = int(pos)
    frac = pos - base
    for idx, w in ((base, 1 - frac), (base + 1, frac)):
        if 0 <= idx < len(buffer):
            buffer[idx][0] += rgb[0] * amount * w
            buffer[idx][1] += rgb[1] * amount * w
            buffer[idx][2] += rgb[2] * amount * w


def draw():
    n = min(NUM_LEDS, num_pixels())

    # turn off anything beyond the first 200 lights, once
    for pixel in pixels():
        if pixel.id >= n:
            pixel.set_rgb(0, 0, 0)

    buffer = [[0.0, 0.0, 0.0] for _ in range(n)]
    rockets = []
    sparks = []

    while True:
        # afterglow / motion blur
        for i in range(n):
            buffer[i][0] *= DECAY
            buffer[i][1] *= DECAY
            buffer[i][2] *= DECAY

        # maybe launch a new rocket
        if len(rockets) < MAX_ROCKETS and random() < LAUNCH_CHANCE:
            rockets.append({
                "pos": 0.0,
                "vel": uniform(ROCKET_MIN_VEL, ROCKET_MAX_VEL),
                "hue": random(),
            })

        # --- update rockets ---
        for rocket in rockets[:]:
            rocket["vel"] += ROCKET_GRAVITY
            rocket["pos"] += rocket["vel"]

            # warm rising trail
            splat(buffer, rocket["pos"], (255, 190, 110), 0.9)

            if rocket["vel"] <= 0.15 or rocket["pos"] >= n - 1:
                # explode into sparks
                num_sparks = randint(*SPARK_COUNT_RANGE)
                for _ in range(num_sparks):
                    hue = (rocket["hue"] + uniform(-0.06, 0.06)) % 1.0
                    life = randint(*SPARK_LIFE_RANGE)
                    sparks.append({
                        "pos": rocket["pos"],
                        "vel": uniform(SPARK_MIN_SPEED, SPARK_MAX_SPEED),
                        "rgb": hsl_to_rgb(hue, 1.0, 0.55),
                        "life": life,
                        "life_max": life,
                    })
                rockets.remove(rocket)

        # --- update sparks ---
        for spark in sparks[:]:
            spark["vel"] += SPARK_GRAVITY
            spark["vel"] *= SPARK_DRAG
            spark["pos"] += spark["vel"]
            spark["life"] -= 1

            if spark["life"] <= 0 or spark["pos"] < -1 or spark["pos"] > n:
                sparks.remove(spark)
                continue

            brightness = spark["life"] / spark["life_max"]
            splat(buffer, spark["pos"], spark["rgb"], brightness)

        # --- write the blended buffer out to the real pixels ---
        for i in range(n):
            r = min(255, buffer[i][0])
            g = min(255, buffer[i][1])
            b = min(255, buffer[i][2])
            pixels(i).set_rgb(int(r), int(g), int(b))

        yield
