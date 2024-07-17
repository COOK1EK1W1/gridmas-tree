import csv
import math


def save_lights(light_locs: list[list[int]]) -> None:
    with open('tree.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(light_locs)


def read_tree_csv() -> list[tuple[float, float, float]]:
    # TODO fix this in the processing stage
    x_off = 0.1
    y_off = 0.17
    with open("tree.csv") as csvfile:
        reader = csv.reader(csvfile)
        list_of_lists: list[tuple[float, float, float]] = []
        for row in reader:
            a = (float(row[0]) + x_off, float(row[1]) + y_off, float(row[2]))
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


def euclidean_distance(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise Exception("mismatch input size")
    total = 0
    for pair in zip(a, b):
        total += (pair[0] - pair[1]) ** 2
    return math.sqrt(total)


def generate_distance_map(coords: list[list[float]]) -> list[list[float]]:
    ret: list[list[float]] = []
    for fr in coords:
        inter: list[float] = []
        for to in coords:
            inter.append(euclidean_distance(fr, to))
        ret.append(inter)
    return ret
