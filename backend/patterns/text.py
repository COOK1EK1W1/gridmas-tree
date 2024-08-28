import cv2
from tree import tree
import numpy as np

name = "Text"
author = "Ciaran"


def run():
    a = -100
    while True:
        a += 1
        text = "hello world"
        scale = 200
        blank_image = np.ones((int(scale * tree.height * 2), int(scale * 2), 3), dtype=np.uint8)


        font = cv2.FONT_HERSHEY_SIMPLEX  # Font type
        font_scale = 10  # Font scale (size)
        font_color = (0, 0, 0)  # Black color in BGR
        thickness = 10  # Thickness of the text

        # Calculate the center of the image to place the text
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]

        cv2.putText(blank_image, text, (-a, int(scale * 1.8)), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        """
        cv2.imshow('Image with Text', blank_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        """

        coords = []

        for pixel in tree.pixels:
            videox = max(min(int((pixel.x + 1) * scale), scale* 2 - 1), 0)
            videoy = max(min(int((tree.height - pixel.z) * scale), scale *tree.height), 0)
            coords.append((videox, videoy))

        for i, pixel in enumerate(tree.pixels):
            value = int(blank_image[coords[i][1]][coords[i][0]][0])
            print(value)
            pixel.set_rgb(value, value, value)
        tree.update()

if __name__ == "__main__":
    run()
