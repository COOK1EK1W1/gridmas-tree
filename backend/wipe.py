"""
Use this module to wipe the tree with color.
P.P.S please do not actually wipe the tree, the LEDs do not like being wet and may produce the magic smoke :wink:
"""

from typing import Callable, Optional
import numpy as np
from gridmas import *


def _rotated_z(theta: float, alpha: float) -> np.ndarray:
    """Compute the rotated Z coordinate for every pixel at once.

    Helper function for wipe() functions

    Args:
        theta (float): Angle in radians
        alpha (float): Angle in radians

    Returns:
        np.ndarray: An (N,) array of rotated Z values, one per pixel, in the
            same order as coords()/pixels()
    """
    xyz = np.asarray(coords(), dtype=np.float64)
    x, y, z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    return np.sin(theta) * (x * np.sin(alpha) + y * np.cos(alpha)) + z * np.cos(theta)


def _set_masked(mask: np.ndarray, color: Color) -> None:
    """Vectorised equivalent of `[set_pixel(i, color) for i in idx]`.

    Directly writes the color into the tree's underlying rgb array for every
    pixel where mask is True, and flags those pixels as changed.

    Args:
        mask (np.ndarray): An (N,) boolean array, True where the pixel should be set
        color (Color): The color to set the masked pixels to
    """
    if not np.any(mask):
        return

    rgb = np.asarray(color.to_tuple(), dtype=np.uint8)
    tree._rgb[mask] = rgb
    tree._changed_arr[mask] = True


def _lerp_masked(mask: np.ndarray, color: Color, frames: int, fn: Callable[[float], float] = linear) -> None:
    """Vectorised equivalent of `[pixels(i).lerp(color, frames, fn=fn) for i in idx]`.

    Mirrors tree.py's module level lerp(), but scoped to only the pixels selected by mask
    instead of the whole tree. Only (re)starts the interpolation for pixels whose target/duration
    actually changed, matching Color.set_lerp()'s no-op-if-unchanged behaviour.

    Args:
        mask (np.ndarray): An (N,) boolean array, True where the pixel should start/continue lerping
        color (Color): The target color to lerp to
        frames (int): The number of frames to lerp over
        fn (Callable[[float], float], optional): Timing function from the Util module. Defaults to linear.
    """
    if not np.any(mask):
        return

    target = np.asarray(color.to_tuple(), dtype=np.uint8)

    changed = mask & (
        np.any(tree._lerp_target != target, axis=1)
        | (tree._lerp_total != frames)
    )

    if not np.any(changed):
        return

    tree._lerp_prev[changed] = tree._rgb[changed]
    tree._lerp_step[changed] = 0
    tree._lerp_target[changed] = target
    tree._lerp_total[changed] = frames
    tree._lerp_fn = fn


def _cont_lerp_masked(mask: np.ndarray) -> None:
    """Vectorised equivalent of `[pixels(i).cont_lerp() for i in idx]`.

    Mirrors tree.py's Tree._advance_all_lerps(), but scoped to only the pixels
    selected by mask instead of every pixel on the tree.

    Args:
        mask (np.ndarray): An (N,) boolean array, True where the pixel's lerp should advance one step
    """
    active = mask & (tree._lerp_step < tree._lerp_total)
    if not np.any(active):
        return

    idx = np.flatnonzero(active)
    tree._lerp_step[idx] += 1

    step = tree._lerp_step[idx].astype(np.float64)
    total = tree._lerp_total[idx].astype(np.float64)

    t = np.divide(step, total, out=np.ones_like(step), where=total != 0)
    t = np.clip(t, 0.0, 1.0)

    eased = tree._lerp_fn(t)[:, None]

    tree._rgb[idx] = np.clip(
        (tree._lerp_prev[idx] + (tree._lerp_target[idx] - tree._lerp_prev[idx]) * eased),
        0,
        255,
    ).astype(np.uint8)


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