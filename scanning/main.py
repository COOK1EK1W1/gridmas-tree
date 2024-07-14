from cv2 import VideoCapture, imwrite, imshow, waitKey, destroyAllWindows
import sys

import requests
import time

print("init camera")

cam_port = 0
cam = VideoCapture(cam_port)

url = "http://192.168.1.50"

print("clearing light")

x = requests.get(url + "/lightoff")
if x.status_code != 200:
    raise Exception("No Light Server")

for d in range(4):
    for a in range(10):
        for x in range(500):
            if x & (1 << a):
                x = requests.get(f"{url}/lighton/{x}")
            else:
                x = requests.get(f"{url}/lightoff/{x}")

        time.sleep(0.5)
        result, image = cam.read()
        time.sleep(0.5)
        imwrite(f"scanning/results/results2-{a}-{d*90}.png", image)

    input("rotate")

"""

time.sleep(0.5)
for d in range(4):
    for i in range(500):
        print(f"locating light {i}", end="\r")
        x = requests.get(f"{url}/lighton/{i}")
        if x.status_code != 200:
            raise Exception("No Light Server")

        time.sleep(0.5)
        result, image = cam.read()
        time.sleep(0.5)

        if result:

            imshow("test", image)
            waitKey(0)
            destroyAllWindows()


            imwrite(f"scanning/results/results-{i}-{d*90}.png", image)

        else:
            raise Exception("camera error")

        x = requests.get(f"{url}/lightoff/{i}")
        if x.status_code != 200:
            raise Exception("No Light Server")
        print(f"Light {i} located  ")
    input("please turn tree")

"""
