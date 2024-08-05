from tree import tree
from colors import Color

name = "Harder Better Faster Stronger"
author = "Ciaran"


def run():
    # each second is 40 frames, the song is 123 bpm which is 41 fps
    tree.set_fps(41)
    tree.sleep(50)

    # count in, 4 white flashes then press play on red
    for _ in range(4):
        tree.fill(Color.white())
        tree.sleep(5)
        tree.fill(Color.black())
        tree.sleep(15)

    tree.fill(Color.red())
    tree.sleep(5)
    tree.fill(Color.black())
    tree.sleep(15)

    # 8 beat intro thing
    tree.sleep(4 * 40 + 20)

    for _ in range(8):
        tree.fill(Color.white())
        tree.sleep(5)
        tree.fill(Color.black())
        tree.sleep(15)

    for _ in range(8):
        tree.fill(Color.red())
        tree.sleep(10)
        tree.fill(Color.green())
        tree.sleep(10)


    for _ in range(8):
        tree.fill(Color.white())
        tree.sleep(5)
        tree.fill(Color.black())
        tree.sleep(15)

    for _ in range(6):
        tree.fill(Color.red())
        tree.sleep(10)
        tree.fill(Color.green())
        tree.sleep(10)

    tree.fill(Color.black())
    for pixel in tree.pixels:
        if pixel.x < 0:
            pixel.set_color(Color.white())
    tree.sleep(10)

    tree.fill(Color.black())
    for pixel in tree.pixels:
        if pixel.x > 0:
            pixel.set_color(Color.white())
    tree.sleep(10)

    tree.fill(Color.black())
    for pixel in tree.pixels:
        if pixel.z < tree.height / 2:
            pixel.set_color(Color.white())
    tree.sleep(10)

    tree.fill(Color.black())
    for pixel in tree.pixels:
        if pixel.z > tree.height / 2:
            pixel.set_color(Color.white())
    tree.sleep(10)
