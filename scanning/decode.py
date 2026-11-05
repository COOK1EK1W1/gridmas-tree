"""Decode which LED is where from photos of gray code patterns.

Each bit is photographed twice, as the pattern and its inverse, so a pixel's bit
is whichever photo it is brighter in. That needs no global threshold, and a pixel
that isn't an LED is about the same in both so it gets rejected.
"""

from typing import Optional

import numpy as np

# a pixel must differ this much between the photos of every bit
MIN_CONTRAST = 30
# and by this fraction of its total brightness, so glow on a bright pixel doesn't count
MIN_BIT_RATIO = 0.2
# pixels with one id further than this from its brightest pixel are ignored
BLOB_RADIUS_PX = 25
MIN_BLOB_PIXELS = 3

# LEDs below this strength are decoded, but only just
LOW_STRENGTH = 50
# compared against the middle of this many LEDs either side along the string
SUSPECT_WINDOW = 3
# how many typical LED spacings from there is too far
SUSPECT_STEPS = 4

# x, y in image pixels and how strongly it decoded
Light = tuple[float, float, float]


def gray_encode(value: int) -> int:
    return value ^ (value >> 1)


def gray_decode(codes: np.ndarray) -> np.ndarray:
    values = codes.copy()
    shifted = codes >> 1
    while shifted.any():
        values ^= shifted
        shifted >>= 1
    return values


def num_bits(light_amount: int) -> int:
    return max(1, (light_amount - 1).bit_length())


def decode_lights(positives: list[np.ndarray], negatives: list[np.ndarray], light_amount: int) -> list[Optional[Light]]:
    """Find every LED from grayscale photos of each bit and its inverse.

    Args:
        positives: photo of the LEDs with each gray code bit set
        negatives: photo of the LEDs with each gray code bit clear
        light_amount: the number of lights

    Returns:
        A location per LED, None for those not seen.
    """
    codes = np.zeros(positives[0].shape, dtype=np.int32)
    strength = np.full(positives[0].shape, 255, dtype=np.int16)
    trusted = np.ones(positives[0].shape, dtype=bool)

    for bit, (positive, negative) in enumerate(zip(positives, negatives)):
        difference = positive.astype(np.int16) - negative.astype(np.int16)
        contrast = np.abs(difference)
        codes |= (difference > 0).astype(np.int32) << bit
        strength = np.minimum(strength, contrast)
        trusted &= contrast >= MIN_BIT_RATIO * (positive.astype(np.int16) + negative.astype(np.int16))

    trusted &= strength >= MIN_CONTRAST

    ys, xs = np.nonzero(trusted)
    ids = gray_decode(codes[trusted])
    weights = strength[trusted].astype(np.float64)

    valid = ids < light_amount
    xs, ys, ids, weights = xs[valid], ys[valid], ids[valid], weights[valid]

    order = np.argsort(ids, kind="stable")
    xs, ys, ids, weights = xs[order], ys[order], ids[order], weights[order]

    lights: list[Optional[Light]] = [None] * light_amount
    unique_ids, starts = np.unique(ids, return_index=True)
    for light, start, end in zip(unique_ids, starts, list(starts[1:]) + [len(ids)]):
        light_xs, light_ys, light_weights = xs[start:end], ys[start:end], weights[start:end]

        # stray pixels that happen to decode to this id can be anywhere, so
        # only the blob around the strongest one counts
        peak = np.argmax(light_weights)
        near = np.hypot(light_xs - light_xs[peak], light_ys - light_ys[peak]) <= BLOB_RADIUS_PX
        if near.sum() < MIN_BLOB_PIXELS:
            continue

        lights[light] = (
            float(np.average(light_xs[near], weights=light_weights[near])),
            float(np.average(light_ys[near], weights=light_weights[near])),
            float(light_weights[peak]),
        )
    return lights


def find_suspects(lights: list[Optional[Light]]) -> list[int]:
    """The ids of LEDs that were found but shouldn't be trusted.

    LEDs are in order along a string, so a location far from the LEDs either
    side of it is a wrong decode. Comparing against the middle of a window
    rather than the two neighbours also catches two bad LEDs in a row.
    """
    found = [i for i, light in enumerate(lights) if light is not None]
    if len(found) < 3:
        return []

    points = np.array([lights[i][:2] for i in found])
    strengths = np.array([lights[i][2] for i in found])
    typical_step = float(np.median(np.hypot(*np.diff(points, axis=0).T)))

    suspects: list[int] = []
    for index, light in enumerate(found):
        start = max(0, index - SUSPECT_WINDOW)
        window = np.delete(points[start:index + SUSPECT_WINDOW + 1], index - start, axis=0)
        distance = np.hypot(*(points[index] - np.median(window, axis=0)))
        if distance > SUSPECT_STEPS * typical_step or strengths[index] < LOW_STRENGTH:
            suspects.append(light)
    return suspects
