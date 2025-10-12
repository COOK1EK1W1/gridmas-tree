from colors import Color
from gridmas import *

name = "Harder Better Faster Stronger"
author = "Ciaran"


def draw():
    # each second is 40 frames, the song is 123 bpm which is 41 fps
    set_fps(41)
    sleep(50)

    # count in, 4 white flashes then press play on red
    for _ in range(4):
        fill(Color.white())
        sleep(5)
        fill(Color.black())
        sleep(15)

    fill(Color.red())
    sleep(5)
    fill(Color.black())
    sleep(15)

    # 8 beat intro thing
    sleep(4 * 40 + 20)

    for _ in range(8):
        fill(Color.white())
        sleep(5)
        fill(Color.black())
        sleep(15)

    for _ in range(8):
        fill(Color.red())
        sleep(10)
        fill(Color.green())
        sleep(10)


    for _ in range(8):
        fill(Color.white())
        sleep(5)
        fill(Color.black())
        sleep(15)

    for _ in range(6):
        fill(Color.red())
        sleep(10)
        fill(Color.green())
        sleep(10)

    fill(Color.black())
    for pixel in pixels():
        if pixel.x < 0:
            pixel.set_color(Color.white())
    sleep(10)

    fill(Color.black())
    for pixel in pixels():
        if pixel.x > 0:
            pixel.set_color(Color.white())
    sleep(10)

    fill(Color.black())
    for pixel in pixels():
        if pixel.z < height() / 2:
            pixel.set_color(Color.white())
    sleep(10)

    fill(Color.black())
    for pixel in pixels():
        if pixel.z > height() / 2:
            pixel.set_color(Color.white())
    sleep(10)
