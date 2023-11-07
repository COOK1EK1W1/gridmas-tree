from cv2 import VideoCapture, destroyWindow, imwrite, imshow, waitKey

import requests
import time

cam_port = 1
cam = VideoCapture(cam_port)


x = requests.get("http://127.0.0.1:5000/lightoff")
if x.status_code != 200:
    raise Exception("No Light Server")

time.sleep(0.5)
for i in range(100):
    print(f"locating light {i}", end="\r")
    x = requests.get(f"http://127.0.0.1:5000/lighton/{i}")
    if x.status_code != 200:
        raise Exception("No Light Server")

    result, image = cam.read()
    time.sleep(0.5)

    if result:

        imshow("test", image)

        waitKey(0)
        destroyWindow("GeeksForGeeks")

        imwrite(f"scanning/results/results-{i}.png", image)

    else:
        raise Exception("camera error")

    x = requests.get(f"http://127.0.0.1:5000/lightoff/{i}")
    if x.status_code != 200:
        raise Exception("No Light Server")
    time.sleep(0.5)
    print(f"Light {i} located  ")
