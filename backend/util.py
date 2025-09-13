"""Holds a bunch of utility functions to make life easier
"""

import csv
import math
from typing import Iterable, Union


def save_lights(light_locs: list[list[int]]) -> None:
    """save_lights Save the loaded tree lights

    Writes the locations of all lights passed into the file tree.csv

    Args:
        light_locs (list[list[int]]): The list of tree light positions
    """
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
    return min(max(val, minv), maxv)

def read_tree_csv(location: str) -> list[tuple[float, float, float]]:
    # TODO fix this in the processing stage
    with open(location) as csvfile:
        reader = csv.reader(csvfile)
        list_of_lists: list[tuple[float, float, float]] = []
        for row in reader:
            a = (float(row[0]), float(row[1]), float(row[2]))
            list_of_lists.append(a)
            """
    ret = []
    for coord in list_of_lists:
        newX = coord[0] * math.cos(math.pi) - coord[1] * math.sin(math.pi)
        newY = coord[1] * math.cos(math.pi) + coord[0] * math.sin(math.pi)
        ret.append(coord)
        ret.append([newX, newY, coord[2]])
            """

    return list_of_lists


def dist(a: Iterable[float], b: Iterable[float]) -> float:
    total = 0
    for pair in zip(a, b):
        total += (pair[0] - pair[1]) ** 2
    return math.sqrt(total)


def linear(x: float) -> float:
    return x


def step(x: float) -> float:
    if x > 0.5:
        return 1
    else:
        return 0


def ease_in_sine(x: float) -> float:
    return 1 - math.cos((x * math.pi) / 2)


def ease_out_sine(x: float) -> float:
    return math.sin((x * math.pi) / 2)


def ease_in_out_sine(x: float) -> float:
    return -(math.cos(math.pi * x) - 1) / 2


def ease_in_cubic(x: float) -> float:
    return x * x * x


def ease_out_cubic(x: float) -> float:
    return 1 - math.pow(1 - x, 3)


def ease_in_out_cubic(x: float) -> float:
    if x < 0.5:
        return 4 * x * x * x
    else:
        return 1 - math.pow(-2 * x + 2, 3) / 2


def ease_in_quint(x: float) -> float:
    return x * x * x * x * x


def ease_out_quint(x: float) -> float:
    return 1 - math.pow(1 - x, 5)


def ease_in_out_quint(x: float) -> float:
    if x < 0.5:
        return 16 * x * x * x * x * x
    else:
        return 1 - math.pow(-2 * x + 2, 5) / 2


def ease_in_circ(x: float) -> float:
    return 1 - math.sqrt(1 - math.pow(x, 2))


def ease_out_circ(x: float) -> float:
    return math.sqrt(1 - math.pow(x - 1, 2))


def ease_in_out_circ(x: float) -> float:
    if x < 0.5:
        return (1 - math.sqrt(1 - math.pow(2 * x, 2))) / 2
    else:
        return (math.sqrt(1 - math.pow(-2 * x + 2, 2)) + 1) / 2


def ease_in_elastic(x: float) -> float:
    c4 = (2 * math.pi) / 3
    if x <= 0:
        return 0
    elif x >= 1:
        return 1
    else:
        return -math.pow(2, 10 * x - 10) * math.sin((x * 10 - 10.75) * c4)


def ease_out_elastic(x: float) -> float:
    c4 = (2 * math.pi) / 3
    if x <= 0:
        return 0
    elif x >= 1:
        return 1
    else:
        return math.pow(2, -10 * x) * math.sin((x * 10 - 0.75) * c4) + 1


def ease_in_out_elastic(x: float) -> float:
    c5 = (2 * math.pi) / 4.5
    if x <= 0:
        return 0
    elif x >= 1:
        return 1
    elif x < 0.5:
        return -(math.pow(2, 20 * x - 10) * math.sin((20 * x - 11.125) * c5)) / 2
    else:
        return (math.pow(2, -20 * x + 10) * math.sin((20 * x - 11.125) * c5)) / 2 + 1


def ease_in_quad(x: float) -> float:
    return x * x


def ease_out_quad(x: float) -> float:
    return 1 - (1 - x) * (1 - x)


def ease_in_out_quad(x: float) -> float:
    if x < 0.5:
        return 2 * x * x
    else:
        return 1 - math.pow(-2 * x + 2, 2) / 2


def ease_in_quart(x: float) -> float:
    return x * x * x * x


def ease_out_quart(x: float) -> float:
    return 1 - math.pow(1 - x, 4)


def ease_in_out_quart(x: float) -> float:
    if x < 0.5:
        return 8 * x * x * x * x * x
    else:
        return 1 - math.pow(-2 * x + 2, 4) / 2


def ease_in_expo(x: float) -> float:
    if x <= 0:
        return 0
    else:
        return math.pow(2, 10 * x - 10)


def ease_out_expo(x: float) -> float:
    if x >= 1:
        return 1
    else:
        return 1 - math.pow(2, -10 * x)


def ease_in_out_expo(x: float) -> float:
    if x <= 0:
        return 0
    elif x >= 1:
        return 1
    elif x < 0.5:
        return math.pow(2, 20 * x - 10) / 2
    else:
        return (2 - math.pow(2, -20 * x + 10)) / 2


def ease_in_back(x: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return c3 * x * x * x - c1 * x * x


def ease_out_back(x: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1

    return 1 + c3 * math.pow(x - 1, 3) + c1 * math.pow(x - 1, 2)


def ease_in_out_back(x: float) -> float:
    c1 = 1.70158
    c2 = c1 * 1.525

    if x < 0.5:
        return (math.pow(2 * x, 2) * ((c2 + 1) * 2 * x - c2)) / 2
    else:
        return (math.pow(2 * x - 2, 2) * ((c2 + 1) * (x * 2 - 2) + c2) + 2) / 2


def ease_in_bounce(x: float) -> float:
    return 1 - ease_out_bounce(1 - x)


def ease_out_bounce(x: float) -> float:
    n1 = 7.5625
    d1 = 2.75

    if (x < 1 / d1):
        return n1 * x * x
    elif (x < 2 / d1):
        x -= 1.5
        return n1 * (x / d1) * x + 0.75
    elif (x < 2.5 / d1):
        x -= 2.25
        return n1 * (x / d1) * x + 0.9375
    else:
        x -= 2.625
        return n1 * (x / d1) * x + 0.984375


def ease_in_out_bounce(x: float) -> float:
    if x < 0.5:
        return (1 - ease_out_bounce(1 - 2 * x)) / 2
    else:
        return (1 + ease_out_bounce(2 * x - 1)) / 2
