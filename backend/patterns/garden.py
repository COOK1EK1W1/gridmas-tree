from gridmas import *
from random import randint, random

# ---------------------------------------------------------------------------
# Garden strip pattern - multi-mode edition (fixed)
#
# draw() is written as a single persistent generator: `while True: ... yield`.
# This is the idiom the docs use for state that must survive between frames -
# because the SAME generator object is resumed every frame, ordinary local
# variables persist automatically, with no need for `global`.
#
# Still linear-only: everything is driven by pixel.id and num_pixels(),
# never x/y/z. No Attributes are used - everything is hard-coded / time-driven.
#
# Cycles automatically through 4 animations, MODE_DURATION seconds each:
#   0. Comet chase   - colored comets bounce along the strip with fading trails
#   1. Theater chase - classic marquee dots marching along, cycling color
#   2. Wipe cascade   - a color fills the strip end-to-end, then resets
#   3. Twinkle field  - organic random sparkle around a drifting base hue
# ---------------------------------------------------------------------------

MODE_DURATION = 12
NUM_MODES = 4


def draw():
    last_mode = -1

    # --- comet chase state ---
    num_comets = 4
    comets = [
        {
            "pos": i / num_comets,
            "vel": (0.006 + i * 0.002) * (1 if i % 2 == 0 else -1),
            "hue": i / num_comets,
        }
        for i in range(num_comets)
    ]

    # --- theater chase state ---
    theater_offset = 0
    theater_hue = 0.0
    theater_tick = 0

    # --- wipe cascade state ---
    wipe_pos = 0.0
    wipe_hue = 0.0

    while True:
        n = num_pixels()
        mode = int(seconds() // MODE_DURATION) % NUM_MODES

        # clear the strip whenever we switch to a new mode
        if mode != last_mode:
            for pixel in pixels():
                pixel.set_rgb(0, 0, 0)
            last_mode = mode

        if mode == 0:
            # ---------------- Comet chase ----------------
            for pixel in pixels():
                pixel.fade(n=1.15)  # dim last frame -> fading trail

            for comet in comets:
                comet["pos"] += comet["vel"]
                if comet["pos"] >= 1.0:
                    comet["pos"] = 1.0
                    comet["vel"] *= -1
                elif comet["pos"] <= 0.0:
                    comet["pos"] = 0.0
                    comet["vel"] *= -1

                head = int(comet["pos"] * (n - 1))
                pixels(head).set_hsl(comet["hue"], 1.0, 0.6)

                tail = head - (1 if comet["vel"] > 0 else -1)
                if 0 <= tail < n:
                    pixels(tail).set_hsl(comet["hue"], 1.0, 0.3)

        elif mode == 1:
            # ---------------- Theater chase ----------------
            spacing = 3
            for pixel in pixels():
                if (pixel.id + theater_offset) % spacing == 0:
                    pixel.set_hsl(theater_hue, 1.0, 0.5)
                else:
                    pixel.set_rgb(0, 0, 0)

            theater_tick += 1
            if theater_tick % 3 == 0:  # advance every 3rd frame - not too fast
                theater_offset = (theater_offset + 1) % spacing
            theater_hue = (theater_hue + 0.003) % 1.0

        elif mode == 2:
            # ---------------- Wipe cascade ----------------
            lit = int(wipe_pos * n)
            for pixel in pixels():
                if pixel.id <= lit:
                    pixel.set_hsl(wipe_hue, 1.0, 0.5)

            wipe_pos += 0.012
            if wipe_pos >= 1.0:
                wipe_pos = 0.0
                wipe_hue = (wipe_hue + 0.17) % 1.0
                for pixel in pixels():
                    pixel.set_rgb(0, 0, 0)

        else:
            # ---------------- Twinkle field ----------------
            base_hue = (seconds() * 0.02) % 1.0
            for pixel in pixels():
                pixel.fade(n=1.08)

            for _ in range(max(1, n // 40)):
                i = randint(0, n - 1)
                hue = (base_hue + (random() - 0.5) * 0.1) % 1.0
                lightness = 0.55 + random() * 0.3
                pixels(i).set_hsl(hue, 0.8, lightness)

        yield
