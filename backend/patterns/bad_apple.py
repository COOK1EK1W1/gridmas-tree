import cv2
from gridmas import *

name = "Bad Apple"
author = "Ciaran"


set_fps(30)
def draw():
    cap = cv2.VideoCapture("patterns/badapple.mp4")
    coords = []

    for pixel in pixels():
        videox = max(min(int(((pixel.x + 1) / 2) * 480), 479), 0)
        videoy = max(min(int((1 - (pixel.z / height())) * 360), 359), 0)
        coords.append((videox, videoy))


    while True:

        ret, frame = cap.read()
        if not ret:
            break

        for i, pixel in enumerate(pixels()):
            value = int(frame[coords[i][1]][coords[i][0]][0])
            pixel.set_rgb(value, value, value)
        yield

    cap.release()
