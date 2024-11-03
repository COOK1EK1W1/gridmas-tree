from typing import Callable
from util import linear
from tree import tree
from colors import Color
import math


def wipe(theta: float, alpha: float, color: Color, speed: int, fade: Color | None = None):
    """Wipe a color from one side to the other. The angle is defined by Theta and Alpha.
       The prefered way to wipe a color on the tree is wipe_frames()

    Args:
        theta (float): Angle in radians
        alpha (float): Angle in radians
        color (Color): The color you are setting
        speed (int): The speed of the animation
        fade (Color | None, optional): Possibly an in between color to be used during the wipe. Defaults to None.
    """
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
    """A more predictable version of wipe().

    Args:
        theta (float): Angle in radians
        alpha (float): Angle in radians
        color (Color): The colour to wipe to
        frames (int, optional): The exact number of frames that the wipe will take to complete. Defaults to 45.
        fade (Color | None, optional): The color the tree goes to after the wipe. Defaults to None.
    """
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
    """Lerp pixels to the target color over the specified number of lerp frames. Produces more of a wave rather than a wipe.

    Args:
        theta (float): Angle in radians
        alpha (float): Angle in radians
        color (Color): The colour to wipe to
        frames (int, optional): The exact number of frames the animation will take to complete. Defaults to 45.
        lerp_frame (int, optional): The number of frames to lerp over. Defaults to 20.
        lerp_fn (Callable[[float], float], optional): Unkown. Defaults to linear.
    """
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
