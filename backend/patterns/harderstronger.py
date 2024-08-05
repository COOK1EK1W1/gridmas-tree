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
    tree.sleep(3 * 40)

    for _ in range(4):
        tree.fill(Color.white())
        tree.sleep(5)
        tree.fill(Color.black())
        tree.sleep(15)

    for _ in range(4):
        tree.fill(Color.white())
        tree.sleep(5)
        tree.fill(Color.black())
        tree.sleep(15)
