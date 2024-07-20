from tree import tree
import cv2

name = "Rick"
author = "Ciaran"


def run():
    cap = cv2.VideoCapture("patterns/rick.mp4")
    while True:

        ret, frame = cap.read()
        if not ret:
            break

        print(tree.height)

        for pixel in tree.pixels:
            videox = max(min(int((pixel.x + 1) * (1280 / 2)), 1279), 0)
            videoy = max(min(int(((tree.height - 0.5) - pixel.z) * 360), 719), 0)
            pixel.set_RGB(*frame[videoy][videox])
        tree.update()

    cap.release()
