from typing import Callable
from util import linear
from tree import tree
from colors import Color
import math


def wipe(theta: float, alpha: float, color: Color, speed: int, fade: Color | None = None):
    # based on Matt Parkers Xmas tree
    coords2 = [[x, y, z] for [x, y, z] in tree.coords]
    for i, coord in enumerate(tree.coords):
        coords2[i][2] = math.sin(theta) * (coord[0] * math.sin(alpha) + coord[1] * math.cos(alpha)) + coord[2] * math.cos(theta)

    minZ = min([x[2] for x in coords2])
    maxZ = max([x[2] for x in coords2])

    for rng in range(int(minZ * 200 - 10), int(maxZ * 200 + 10), speed):
        for i, coord in enumerate(coords2):
            if rng <= coord[2] * 200 < rng + 10:
                tree.set_light(i, color)
            else:
                if fade:
                    tree.get_light(i).lerp(fade.to_tuple(), 50)
        tree.update()


def wipe_frames(theta: float, alpha: float, color: Color, frames: int = 45, fade: Color | None = None):
    # based on Matt Parkers Xmas tree
    coords2 = [[x, y, z] for [x, y, z] in tree.coords]
    for i, coord in enumerate(tree.coords):
        coords2[i][2] = math.sin(theta) * (coord[0] * math.sin(alpha) + coord[1] * math.cos(alpha)) + coord[2] * math.cos(theta)

    minZ = min([x[2] for x in coords2])
    maxZ = max([x[2] for x in coords2])
    slice_width = (maxZ - minZ) / frames

    for slice in range(frames):
        slice_min = slice * slice_width + minZ
        slice_max = (slice + 1) * slice_width + minZ
        for i, coord in enumerate(coords2):
            if slice_min <= coord[2] <= slice_max:
                tree.set_light(i, color)
            else:
                if fade:
                    tree.get_light(i).lerp(fade.to_tuple(), 50)
        tree.update()


def wipe_wave_frames(theta: float, alpha: float, color: Color, frames: int = 45, lerp_frame: int = 20, lerp_fn: Callable[[float], float] = linear):
    # based on Matt Parkers Xmas tree
    coords2 = [[x, y, z] for [x, y, z] in tree.coords]
    for i, coord in enumerate(tree.coords):
        coords2[i][2] = math.sin(theta) * (coord[0] * math.sin(alpha) + coord[1] * math.cos(alpha)) + coord[2] * math.cos(theta)

    minZ = min([x[2] for x in coords2])
    maxZ = max([x[2] for x in coords2])
    slice_width = (maxZ - minZ) / frames

    for slice in range(frames):
        slice_min = slice * slice_width + minZ
        slice_max = (slice + 1) * slice_width + minZ
        for i, coord in enumerate(coords2):
            if slice_min <= coord[2] <= slice_max:
                tree.get_light(i).lerp(color.to_tuple(), lerp_frame, fn=lerp_fn)
            else:
                tree.get_light(i).cont_lerp()
        tree.update()
