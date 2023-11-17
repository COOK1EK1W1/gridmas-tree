from cv2 import VideoCapture, destroyWindow, imwrite, imshow, waitKey

import requests
import time

print("init camera")


print("clearing light")
x = requests.get("http://192.168.1.50:5000/lightoff")
if x.status_code != 200:
    raise Exception("No Light Server")


lol = [(657, 668), (729, 692), (724, 661), (658, 597), (668, 535), (648, 491), (671, 420), (674, 368), (691, 338), (659, 266), (648, 315), (643, 379), (622, 434), (628, 493), (636, 561), (596, 611), (554, 622), (488, 621), (466, 581), (473, 524), (435, 492), (444, 423), (449, 372), (414, 326), (404, 277),
       (436, 234), (400, 179), (438, 194), (487, 200), (538, 251), (606, 239), (638, 276), (698, 251), (752, 245), (787, 214), (822, 185), (824, 240), (846, 280), (818, 307), (843, 386), (809, 426), (820, 469), (800, 493), (713, 482), (696, 456), (734, 378), (721, 334), (704, 303), (704, 285), (676, 310)]

lights = list(zip(range(50), lol))
lights.sort(key=lambda x: x[1][0])
print(lights)
colours = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
t = 0
while True:
    lights.sort(key=lambda x: x[1][0])
    t = (t + 1) % 3
    for i in lights:
        x = requests.get(
            f"http://192.168.1.50:5000/lighton/{i[0]}")
    for i in lights:
        x = requests.get(
            f"http://192.168.1.50:5000/lightoff/{i[0]}")
    lights.sort(key=lambda x: x[1][1])
    t = (t + 1) % 3
    for i in lights:
        x = requests.get(
            f"http://192.168.1.50:5000/lighton/{i[0]}")
    for i in lights:
        x = requests.get(
            f"http://192.168.1.50:5000/lightoff/{i[0]}")
