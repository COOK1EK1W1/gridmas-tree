"""
Use this module to wipe the tree with color.
P.P.S please do not actually wipe the tree, the LEDs do not like being wet and may produce the magic smoke :wink:
"""

from typing import Callable, Optional
import numpy as np
from gridmas import *
from tree import _rotated_z, _set_masked, _lerp_masked, _cont_lerp_masked


def wipe(theta: float, alpha: float, color: Color, speed: int, fade: Optional[Color] = None):
    """wipe A simple wipe

    Wipe a color from one side to the other. The angle is defined by Theta and Alpha.
    The prefered way to wipe a color on the tree is wipe_frames()

    Args:
        theta (float): Angle in radians
        alpha (float): Angle in radians
        color (Color): The color you are setting
        speed (int): The speed of the animation
        fade (Color | None, optional): Possibly an in between color to be used during the wipe. Defaults to None.

    Note:
        The outer `for rng in range(...)` loop below is the frame stepper —
        it has to remain a loop because each iteration must `yield` a
        separate animation frame. Everything that happens *within* a frame
        (the coordinate transform and the per-pixel condition check, as well
        as the actual color/lerp writes) is vectorised with numpy masks
        instead of looping over pixels.
    """
    # based on Matt Parkers Xmas tree
    scaled_z = _rotated_z(theta, alpha) * 200

    min_z = scaled_z.min()
    max_z = scaled_z.max()

    for rng in range(int(min_z - 10), int(max_z + 10), speed):
        lit_mask = (scaled_z >= rng) & (scaled_z < rng + 10)

        _set_masked(lit_mask, color)

        if fade:
            _lerp_masked(~lit_mask, fade, 50)

        yield


def wipe_frames(theta: float, alpha: float, color: Color, frames: int = 45, fade: Optional[Color] = None):
    """wipe_frames wipe for n number of frames

    A more predictable version of wipe().

    Args:
        theta (float): Angle in radians
        alpha (float): Angle in radians
        color (Color): The colour to wipe to
        frames (int, optional): The exact number of frames that the wipe will take to complete. Defaults to 45.
        fade (Color | None, optional): The color the tree goes to after the wipe. Defaults to None.
    """
    # based on Matt Parkers Xmas tree
    rotated_z = _rotated_z(theta, alpha)

    min_z = rotated_z.min()
    max_z = rotated_z.max()
    slice_width = (max_z - min_z) / frames

    # all slice boundaries computed up-front, vectorised, instead of per-frame arithmetic
    slice_edges = min_z + np.arange(frames + 1) * slice_width

    for slice_idx in range(frames):
        slice_min = slice_edges[slice_idx]
        slice_max = slice_edges[slice_idx + 1]

        lit_mask = (rotated_z >= slice_min) & (rotated_z <= slice_max)

        _set_masked(lit_mask, color)

        if fade:
            _lerp_masked(~lit_mask, fade, 50)

        yield


def wipe_wave_frames(theta: float, alpha: float, color: Color, frames: int = 45, lerp_frame: int = 20, lerp_fn: Callable[[float], float] = linear):
    """wipe_wave_frames Wave for a number of frames

    Lerp pixels to the target color over the specified number of lerp frames. Produces more of a wave rather than a wipe.

    Args:
        theta (float): Angle in radians
        alpha (float): Angle in radians
        color (Color): The colour to wipe to
        frames (int, optional): The exact number of frames the animation will take to complete. Defaults to 45.
        lerp_frame (int, optional): The number of frames to lerp over. Defaults to 20.
        lerp_fn (Callable[[float], float], optional): Unkown. Defaults to linear.
    """
    # based on Matt Parkers Xmas tree
    rotated_z = _rotated_z(theta, alpha)

    min_z = rotated_z.min()
    max_z = rotated_z.max()
    slice_width = (max_z - min_z) / frames

    slice_edges = min_z + np.arange(frames + 1) * slice_width

    for slice_idx in range(frames):
        slice_min = slice_edges[slice_idx]
        slice_max = slice_edges[slice_idx + 1]

        wave_mask = (rotated_z >= slice_min) & (rotated_z <= slice_max)

        _lerp_masked(wave_mask, color, lerp_frame, fn=lerp_fn)
        _cont_lerp_masked(~wave_mask)

        yield