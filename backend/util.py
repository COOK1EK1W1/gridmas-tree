"""Holds a bunch of utility functions to make life easier
"""

import csv
import math
import numpy as np
from typing import Iterable, Union


def save_lights(light_locs: list[list[int]]) -> None:
    with open('tree.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(light_locs)

class tcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


PI = 3.1415926535897932384626433832795028841971693993

HALF_PI = PI/2

TWO_PI = PI*2

TAU = PI * 2


def clamp(val: Union[float, int], minv: Union[float, int], maxv: Union[float, int]):
    """Clamp a value between two values

        example:
            ```
            clamp(-1, 0, 1) # 0
            clamp(2, 0, 1) # 1
            clamp(0.5, 0, 1) # 0.5
            ```

    """
    return min(max(val, minv), maxv)

def read_tree_csv(location: str) -> list[tuple[float, float, float]]:
    with open(location, newline="") as csvfile:
        reader = csv.reader(csvfile)
        f = float
        return [(f(a), f(b), f(c)) for a, b, c in reader]


def dist(a: Iterable[float], b: Iterable[float]) -> float:
    """The distance between two vectors

        example:
            ```
            dist([0, 0], [3, 4]) # 5
            ```
    """ 
    total = 0
    for pair in zip(a, b):
        total += (pair[0] - pair[1]) ** 2
    return math.sqrt(total)


def linear(x: float) -> float:
    """The linear activation function

    Activation function can be used with lerp to achieve different interpolations.

    The activations are taken from https://easings.net/# and are similar to the CSS implementations
    """
    return x


def step(x: float) -> float:
    """The step activation function"""
    x = np.asarray(x)
    return np.where(x > 0.5, 1, 0)


def ease_in_sine(x: float) -> float:
    """The ease in sine activation function"""
    x = np.asarray(x)
    return 1 - np.cos((x * np.pi) / 2)


def ease_out_sine(x: float) -> float:
    """The ease out sine activation function"""
    x = np.asarray(x)
    return np.sin((x * np.pi) / 2)


def ease_in_out_sine(x: float) -> float:
    """The ease in out sine activation function"""
    x = np.asarray(x)
    return -(np.cos(np.pi * x) - 1) / 2


def ease_in_cubic(x: float) -> float:
    """The ease in cubic activation function"""
    x = np.asarray(x)
    return x * x * x


def ease_out_cubic(x: float) -> float:
    """The ease out cubic activation function"""
    x = np.asarray(x)
    return 1 - np.power(1 - x, 3)


def ease_in_out_cubic(x: float) -> float:
    """The ease in out cubic activation function"""
    x = np.asarray(x)
    return np.where(x < 0.5, 4 * x * x * x, 1 - np.power(-2 * x + 2, 3) / 2)


def ease_in_quint(x: float) -> float:
    """The ease in quint activation function"""
    x = np.asarray(x)
    return x * x * x * x * x


def ease_out_quint(x: float) -> float:
    """The ease out quint activation function"""
    x = np.asarray(x)
    return 1 - np.power(1 - x, 5)


def ease_in_out_quint(x: float) -> float:
    """The ease in out quint activation function"""
    x = np.asarray(x)
    return np.where(x < 0.5, 16 * x * x * x * x * x, 1 - np.power(-2 * x + 2, 5) / 2)


def ease_in_circ(x: float) -> float:
    """The ease in circle activation function"""
    x = np.asarray(x)
    return 1 - np.sqrt(1 - np.power(x, 2))


def ease_out_circ(x: float) -> float:
    """The ease out circle activation function"""
    x = np.asarray(x)
    return np.sqrt(1 - np.power(x - 1, 2))


def ease_in_out_circ(x: float) -> float:
    """The ease in out circle activation function"""
    x = np.asarray(x)
    # clip before sqrt: np.where evaluates both branches eagerly (unlike
    # Python's if/else), so the untaken branch can otherwise go slightly
    # negative under sqrt right at the x=0/x=1 edges and warn/NaN even
    # though that value is discarded either way
    lower = (1 - np.sqrt(np.clip(1 - np.power(2 * x, 2), 0, None))) / 2
    upper = (np.sqrt(np.clip(1 - np.power(-2 * x + 2, 2), 0, None)) + 1) / 2
    return np.where(x < 0.5, lower, upper)


def ease_in_elastic(x: float) -> float:
    """The ease in elastic activation function"""
    x = np.asarray(x, dtype=np.float64)
    c4 = (2 * np.pi) / 3
    body = -np.power(2.0, 10 * x - 10) * np.sin((x * 10 - 10.75) * c4)
    return np.where(x <= 0, 0, np.where(x >= 1, 1, body))


def ease_out_elastic(x: float) -> float:
    """The ease out elastic activation function"""
    x = np.asarray(x, dtype=np.float64)
    c4 = (2 * np.pi) / 3
    body = np.power(2.0, -10 * x) * np.sin((x * 10 - 0.75) * c4) + 1
    return np.where(x <= 0, 0, np.where(x >= 1, 1, body))


def ease_in_out_elastic(x: float) -> float:
    """The ease in out elastic activation function"""
    x = np.asarray(x, dtype=np.float64)
    c5 = (2 * np.pi) / 4.5
    lower = -(np.power(2.0, 20 * x - 10) * np.sin((20 * x - 11.125) * c5)) / 2
    upper = (np.power(2.0, -20 * x + 10) * np.sin((20 * x - 11.125) * c5)) / 2 + 1
    body = np.where(x < 0.5, lower, upper)
    return np.where(x <= 0, 0, np.where(x >= 1, 1, body))


def ease_in_quad(x: float) -> float:
    """The ease in quad activation function"""
    x = np.asarray(x)
    return x * x


def ease_out_quad(x: float) -> float:
    """The ease out quad activation function"""
    x = np.asarray(x)
    return 1 - (1 - x) * (1 - x)


def ease_in_out_quad(x: float) -> float:
    """The ease in out quad activation function"""
    x = np.asarray(x)
    return np.where(x < 0.5, 2 * x * x, 1 - np.power(-2 * x + 2, 2) / 2)


def ease_in_quart(x: float) -> float:
    """The ease in quart activation function"""
    x = np.asarray(x)
    return x * x * x * x


def ease_out_quart(x: float) -> float:
    """The ease out quart activation function"""
    x = np.asarray(x)
    return 1 - np.power(1 - x, 4)


def ease_in_out_quart(x: float) -> float:
    """The ease in out quart activation function"""
    x = np.asarray(x)
    return np.where(x < 0.5, 8 * x * x * x * x, 1 - np.power(-2 * x + 2, 4) / 2)


def ease_in_expo(x: float) -> float:
    """The ease in expo activation function"""
    x = np.asarray(x, dtype=np.float64)
    return np.where(x <= 0, 0, np.power(2.0, 10 * x - 10))


def ease_out_expo(x: float) -> float:
    """The ease out expo activation function"""
    x = np.asarray(x, dtype=np.float64)
    return np.where(x >= 1, 1, 1 - np.power(2.0, -10 * x))


def ease_in_out_expo(x: float) -> float:
    """The ease in out expo activation function"""
    x = np.asarray(x, dtype=np.float64)
    body = np.where(x < 0.5, np.power(2.0, 20 * x - 10) / 2, (2 - np.power(2.0, -20 * x + 10)) / 2)
    return np.where(x <= 0, 0, np.where(x >= 1, 1, body))


def ease_in_back(x: float) -> float:
    """The ease in back activation function"""
    x = np.asarray(x)
    c1 = 1.70158
    c3 = c1 + 1
    return c3 * x * x * x - c1 * x * x


def ease_out_back(x: float) -> float:
    """The ease out back activation function"""
    x = np.asarray(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * np.power(x - 1, 3) + c1 * np.power(x - 1, 2)


def ease_in_out_back(x: float) -> float:
    """The ease in out back activation function"""
    x = np.asarray(x)
    c1 = 1.70158
    c2 = c1 * 1.525
    return np.where(
        x < 0.5,
        (np.power(2 * x, 2) * ((c2 + 1) * 2 * x - c2)) / 2,
        (np.power(2 * x - 2, 2) * ((c2 + 1) * (x * 2 - 2) + c2) + 2) / 2,
    )


def ease_in_bounce(x: float) -> float:
    """The ease in bounce activation function"""
    return 1 - ease_out_bounce(1 - np.asarray(x))


def ease_out_bounce(x: float) -> float:
    """The ease out bounce activation function"""
    x = np.asarray(x, dtype=np.float64)
    n1 = 7.5625
    d1 = 2.75

    xa = x
    ra = n1 * xa * xa

    xb = x - 1.5
    rb = n1 * (xb / d1) * xb + 0.75

    xc = x - 2.25
    rc = n1 * (xc / d1) * xc + 0.9375

    xd = x - 2.625
    rd = n1 * (xd / d1) * xd + 0.984375

    return np.select(
        [x < 1 / d1, x < 2 / d1, x < 2.5 / d1],
        [ra, rb, rc],
        default=rd,
    )


def ease_in_out_bounce(x: float) -> float:
    """The ease in out bounce activation function"""
    x = np.asarray(x)
    return np.where(
        x < 0.5,
        (1 - ease_out_bounce(1 - 2 * x)) / 2,
        (1 + ease_out_bounce(2 * x - 1)) / 2,
    )