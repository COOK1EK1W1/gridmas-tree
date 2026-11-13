from gridmas import *
from fixture import Graph
from house_fixtures import attach, fence_graph, front_graph

name = "Graph Check"
author = "Ciaran"

# Each edge gets its own colour, dim at its start vertex and bright at its end, and the
# pixels at vertices blink white. A pixel that stays dark is on no edge or vertex, a
# colour running the wrong way or spilling onto another wire points at a mistake in the file.

BLINK_FRAMES = 20


def draw_graph():
    all_edges = edges()
    for edge in all_edges:
        hue = edge.id / len(all_edges)
        for pixel, t in zip(edge.pixels, edge.t):
            pixel.set_hsl(hue, 1, 0.1 + 0.4 * t)

    if frame() % (BLINK_FRAMES * 2) < BLINK_FRAMES:
        for vertex in vertices():
            for pixel in vertex.pixels:
                pixel.set_rgb(255, 255, 255)


attach()
fence_graph.set_draw_fn(draw_graph)
front_graph.set_draw_fn(draw_graph)

def display_update():
    pass
