import neopixel
import os
import time
import board
import random
from dotenv import load_dotenv
import csv
import math

load_dotenv()
pixel_pin = board.D18
pixel_num = int(os.getenv("PIXELS"))
print(pixel_num)
pixels = neopixel.NeoPixel(pixel_pin, pixel_num, auto_write=False)

lights = []


def turnOnLight(n: int, colour: tuple[int] = (255, 255, 255)):
    pixels[n] = colour


def turnOffLight(n: int):
    pixels[n] = (0, 0, 0)

def savelights(lightLocs):
    with open('bruh.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(lightLocs)

def update():
    pixels.show()

def doStandard(n: int):
    for _ in range(n):
        for i in range(pixel_num):
            pixels[i] = (255, 255, 255)
            for ia in range(pixel_num):
                r, g, b = pixels[ia]
                pixels[ia] = (r/1.1, g/1.1, b/1.1)
            pixels.show()
            time.sleep(0.01)


def read_csv():
    with open("bruh.csv") as csvfile:
        reader = csv.reader(csvfile)
        list_of_lists = [[int(item) for item in row] for row in reader]
    return list_of_lists

def doCool(n: int):
    lol = read_csv()
    j = 1.1
    fps = 1/60
    rng = 10
    for idk in range(n * 3):
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        for i in range(min(lol, key=lambda x: x[idk%3])[idk%3], max(lol, key=lambda x: x[idk%3])[idk%3], rng):
            for ia, light in enumerate(lol):
                if i <= light[idk%3] < i + rng:
                    pixels[ia] = color
                else:
                    r, g, b = pixels[ia]
                    pixels[ia] = (r/j, g/j, b/j)
            pixels.show()
            time.sleep(fps)
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))

def doSpin():
    coords = read_csv()
    heights = []
    for i in coords:
        heights.append(i[2])

    min_alt = min(heights)
    max_alt = max(heights)

    # VARIOUS SETTINGS
    buffer = 200

    # how much the rotation points moves each time
    dinc = 1

    angle = 0
    
    # how much the angle changes per cycle
    inc = 0.1
    
    # the two colours in GRB order
    # if you are turning a lot of them on at once, keep their brightness down please
    colourA = [0,50,50] # purple
    colourB = [50,50,0] # yellow
    
    
    # INITIALISE SOME VALUES
    
    swap01 = 0
    swap02 = 0
    
    # direct it move in
    direction = -1
    
    # the starting point on the vertical axis
    c = 100 
    while True:
        time.sleep(0.05)

        LED = 0
        while LED < len(coords):
            if math.tan(angle)*coords[LED][1] <= coords[LED][2]+c:
                pixels[LED] = colourA
            else:
                pixels[LED] = colourB
            LED += 1

        # use the show() option as rarely as possible as it takes ages
        # do not use show() each time you change a LED but rather wait until you have changed them all
        pixels.show()

        # now we get ready for the next cycle

        angle += inc
        if angle > 2*math.pi:
            angle -= 2*math.pi
            swap01 = 0
            swap02 = 0

        # this is all to keep track of which colour is 'on top'

        if angle >= 0.5*math.pi:
            if swap01 == 0:
                colour_hold = [i for i in colourA]
                colourA =[i for i in colourB]
                colourB = [i for i in colour_hold]
                swap01 = 1

        if angle >= 1.5*math.pi:
            if swap02 == 0:
                colour_hold = [i for i in colourA]
                colourA =[i for i in colourB]
                colourB = [i for i in colour_hold]
                swap02 = 1

