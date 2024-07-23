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

    while True:

        ret, frame = cap.read()
        if not ret:
            break

        for i, pixel in enumerate(tree.pixels):
            if 0.5 < pixel.z < 2.5:
                pixel.set_RGB(*frame[coords[i][1]][coords[i][0]])
            else:
                pixel.set_RGB(0, 0, 0)
        tree.update()

    cap.release()
