# text
```py linenums="1"
import cv2
from gridmas import *
import numpy as np

name = "Text"
author = "Ciaran"


def draw():
    a = -500

    new_coords = []
    text = "(Black screen with text; The sound of buzzing bees can be heard)According to all known laws of aviation, : there is no way a bee should be able to fly. : Its wings are too small to get its fat little body off the ground. : The bee, of course, flies anyway : because bees don't care what humans think is impossible."
    scale = 100

    for pixel in pixels():
        videox = max(min(int((pixel.x + 1) * scale), scale * 2 - 1), 0)
        videoy = max(min(int((height() - pixel.z) * scale), int(scale * height() - 1)), 0)
        new_coords.append((videox, videoy))

    font = cv2.FONT_HERSHEY_SIMPLEX  # Font type
    font_scale = int(height() * scale * 0.03)  # Font scale (size)
    font_color = (0, 0, 0)  # Black color in BGR
    thickness = int(height() * scale * 0.1)  # Thickness of the text

    while True:
        a += 5
        blank_image = np.ones((int(scale * height()), int(scale * 2), 3), dtype=np.uint8)



        # Calculate the center of the image to place the text
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]

        cv2.putText(blank_image, text, (-a, int(scale * height() * 0.8)), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        """
        cv2.imshow('Image with Text', blank_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        """

        for i, pixel in enumerate(pixels()):
            value = int(blank_image[new_coords[i][1]][new_coords[i][0]][0])
            pixel.set_rgb(value, value, value)
        yield

```