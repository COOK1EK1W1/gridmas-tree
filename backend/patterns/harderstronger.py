from colors import Color
from gridmas import *

name = "Harder Better Faster Stronger"
author = "Ciaran"

# not in git, put the song next to this file
set_music("harderstronger.mp3")

# the song is 123 bpm, at 41 fps each beat is 20 frames
set_fps(41)


def draw():
    # first beat of the song, then the 8 beat intro thing
    yield from sleep(10 * 20)

    for _ in range(8):
        fill(Color.white())
        yield from sleep(5)
        fade()
        yield from sleep(15)

    for _ in range(8):
        fill(Color.red())
        yield from sleep(10)
        fill(Color.green())
        yield from sleep(10)


    for _ in range(8):
        fill(Color.white())
        yield from sleep(5)
        fade()
        yield from sleep(15)

    for _ in range(6):
        fill(Color.red())
        yield from sleep(10)
        fill(Color.green())
        yield from sleep(10)

    fill(Color.black())
    for pixel in pixels():
        if pixel.x < 0:
            pixel.set_color(Color.white())
    yield from sleep(10)

    fill(Color.black())
    for pixel in pixels():
        if pixel.x > 0:
            pixel.set_color(Color.white())
    yield from sleep(10)

    fill(Color.black())
    for pixel in pixels():
        if pixel.z < height() / 2:
            pixel.set_color(Color.white())
    yield from sleep(10)

    fill(Color.black())
    for pixel in pixels():
        if pixel.z > height() / 2:
            pixel.set_color(Color.white())
    yield from sleep(10)

    # the choreography is done, stay dark for the rest of the song
    fill(Color.black())
    while True:
        yield
