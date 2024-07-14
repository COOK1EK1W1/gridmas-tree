import csv
import math


def savelights(lightLocs: list[list[int]]) -> None:
    with open('tree.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(lightLocs)


def read_tree_csv() -> list[list[float]]:
    with open("tree.csv") as csvfile:
        reader = csv.reader(csvfile)
        list_of_lists = [[float(item) for item in row] for row in reader]
    return list_of_lists


def pythagorasDistance(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise Exception("mismatch input size")
    total = 0
    for pair in zip(a, b):
        total += (pair[0] - pair[1]) ** 2
    return math.sqrt(total)


def generateDistances(coords) -> list[list[float]]:
    ret = []
    for fr in coords:
        inter = []
        for to in coords:
            inter.append(pythagorasDistance(fr, to))
        ret.append(inter)
    return ret
