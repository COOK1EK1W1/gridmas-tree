# Bad Apple

A demonstration of how to load a video file and play it on the tree by _Ciaran_

```py linenums="1"
from tree import tree
import cv2

name = "Bad Apple"
author = "Ciaran"


def run():
    cap = cv2.VideoCapture("patterns/badapple.mp4")
    coords = []

    for pixel in tree.pixels:
        videox = max(min(int(((-pixel.x + 1) / 2) * 480), 479), 0)
        videoy = max(min(int((1 - pixel.z / 2) * 360), 359), 0)
        coords.append((videox, videoy))

    tree.set_fps(30)

    while True:

        ret, frame = cap.read()
        if not ret:
            break

        for i, pixel in enumerate(tree.pixels):
            if 0.5 < pixel.z < 2.5:
                value = int(frame[coords[i][1]][coords[i][0]][0])
                pixel.set_rgb(value, value, value)

            else:
                pixel.set_rgb(0, 0, 0)
        tree.update()

    cap.release()

```