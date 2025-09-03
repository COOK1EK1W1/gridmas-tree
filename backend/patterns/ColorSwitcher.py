from attribute import ColorAttr
from colors import Color
from tree import tree

name = "Color Switcher"
author = "Murtaza"
num_colors = 2

def draw():
    tree.set_fps(1)
    colors = [Color.random() for i in range(num_colors)]
    while True:
        for pixel_index, pixel in enumerate(tree.pixels):
            for color_index, color in enumerate(colors):
                if pixel_index % num_colors == color_index:
                    pixel.set_color(color)
        yield
        colors = [Color.different_from(color) for color in colors]
