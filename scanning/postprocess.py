"""Tidy up fused LED positions using the order LEDs sit in along the string."""

from typing import Optional

import numpy as np

Position = tuple[float, float, float]
PartialPosition = tuple[Optional[float], Optional[float], Optional[float]]


def fill_missing(positions: list[PartialPosition]) -> list[Position]:
    """Linearly interpolate each unknown axis between the known LEDs either side.

    An axis is filled on its own, as an LED may be seen by only some views.
    LEDs at the ends of the string have one known side so copy it, and an axis
    no LED has, like depth in a single view scan, is left at 0.
    """
    values = np.array(positions, dtype=np.float64).reshape(-1, 3)
    indices = np.arange(len(values))
    for axis in range(3):
        known = ~np.isnan(values[:, axis])
        if known.any():
            values[:, axis] = np.interp(indices, indices[known], values[known, axis])
        else:
            values[:, axis] = 0
    return [(float(x), float(y), float(z)) for x, y, z in values]


def find_outliers(positions: list[Position], percent: float) -> list[int]:
    """The top percent of LEDs by how far they take the string out of its way.

    An LED scores the extra distance it adds over its neighbours joining up
    directly. Unlike the raw distances, that stays low for a correct LED next
    to a bad one, and for a long straight run between evenly spaced LEDs.
    The two end LEDs have no neighbours to interpolate between so never count.
    """
    amount = round(len(positions) * percent / 100)
    if amount <= 0 or len(positions) < 3:
        return []

    points = np.array(positions)
    to_previous = np.linalg.norm(points[1:-1] - points[:-2], axis=1)
    to_next = np.linalg.norm(points[2:] - points[1:-1], axis=1)
    direct = np.linalg.norm(points[2:] - points[:-2], axis=1)
    detour = to_previous + to_next - direct

    worst = np.argsort(detour)[::-1][:amount]
    return sorted(int(index) + 1 for index in worst)


def clean_positions(positions: list[PartialPosition], percent: float) -> tuple[list[Position], list[int]]:
    """Fill in unseen LEDs and replace the worst outliers, returning those outliers too.

    Filling happens again once the outliers are known so that an unseen LED
    next to an outlier isn't left interpolated from its bad position.
    """
    outliers = set(find_outliers(fill_missing(positions), percent))
    kept: list[PartialPosition] = [(None, None, None) if i in outliers else position for i, position in enumerate(positions)]
    return fill_missing(kept), sorted(outliers)


def scale_locations_to_GIFT(locations: list[Position]) -> list[Position]:
    """Put the middle of the tree on the z axis, its widest axis on -1 to 1 and its lowest LED at z 0"""
    points = np.array(locations)
    lowest = points.min(axis=0)
    highest = points.max(axis=0)
    middle = (lowest + highest) / 2

    scale_factor = 2 / max(highest[0] - lowest[0], highest[1] - lowest[1])

    return [
        (float((x - middle[0]) * scale_factor), float((y - middle[1]) * scale_factor), float((z - lowest[2]) * scale_factor))
        for x, y, z in points
    ]
