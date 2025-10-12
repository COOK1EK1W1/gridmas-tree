from gridmas import *

name = "Color Switcher"
author = "Murtaza"
num_colors = 2

set_fps(1)

def draw():
    
    colors = [Color.random() for i in range(num_colors)]
    while True:
        for pixel_index, pixel in enumerate(pixels()):
            for color_index, color in enumerate(colors):
                if pixel_index % num_colors == color_index:
                    pixel.set_color(color)
        yield
        for _ in range(45):
            yield
        colors = [Color.different_from(color) for color in colors]
