import neopixel
import os
import time
import board
import random
from dotenv import load_dotenv

load_dotenv()
pixel_pin = board.D18
pixel_num = os.getenv("PIXELS")
pixels = neopixel.NeoPixel(pixel_pin, pixel_num, auto_write=False)


def turnOnLight(n: int, colour: tuple[int] = (255, 255, 255)):
    pixels[n] = colour


def turnOffLight(n: int):
    pixels[n] = (0, 0, 0)


def doCool(n: int):
    lol = [(657, 668), (729, 692), (724, 661), (658, 597), (668, 535), (648, 491), (671, 420), (674, 368), (691, 338), (659, 266), (648, 315), (643, 379), (622, 434), (628, 493), (636, 561), (596, 611), (554, 622), (488, 621), (466, 581), (473, 524), (435, 492), (444, 423), (449, 372), (414, 326), (404, 277),
           (436, 234), (400, 179), (438, 194), (487, 200), (538, 251), (606, 239), (638, 276), (698, 251), (752, 245), (787, 214), (822, 185), (824, 240), (846, 280), (818, 307), (843, 386), (809, 426), (820, 469), (800, 493), (713, 482), (696, 456), (734, 378), (721, 334), (704, 303), (704, 285), (676, 310)]

    for _ in range(n):
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        for i in range(min(lol, key=lambda x: x[0])[0], max(lol, key=lambda x: x[0])[0], 20):
            for ia, light in enumerate(lol):
                if i < light[0] < i + 40:
                    pixels[ia] = color
                else:
                    r, g, b = pixels[ia]
                    pixels[ia] = (r/1.5, g/1.5, b/1.5)
            pixels.show()
            time.sleep(1/30)
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        for i in range(min(lol, key=lambda x: x[1])[1], max(lol, key=lambda x: x[1])[1], 20):
            for ia, light in enumerate(lol):
                if i < light[1] < i + 40:
                    pixels[ia] = color
                else:
                    r, g, b = pixels[ia]
                    pixels[ia] = (r/1.5, g/1.5, b/1.5)
            pixels.show()
            time.sleep(1/30)
