import neopixel
import os
import board
from dotenv import load_dotenv
import csv

load_dotenv()
pixel_pin = board.D18
envpixels = os.getenv("PIXELS")

if envpixels == None:
    raise Exception("No env variable")

pixel_num = int(envpixels)
pixels = neopixel.NeoPixel(pixel_pin, pixel_num, auto_write=False)

lights = []


def setLight(n: int, colour: tuple[int, int, int] = (255, 255, 255)):
    pixels[n] = colour


def get_light(n: int) -> tuple[int, int, int]:
    return pixels[n]


def turnOffLight(n: int):
    pixels[n] = (0, 0, 0)


def savelights(lightLocs: list[list[int]]) -> None:
    with open('bruh.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(lightLocs)


def update():
    pixels.show()


def read_csv():
    with open("bruh.csv") as csvfile:
        reader = csv.reader(csvfile)
        list_of_lists = [[int(item) for item in row] for row in reader]
    return list_of_lists
