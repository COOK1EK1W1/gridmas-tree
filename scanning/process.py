import requests
from point import Point
import os
from dotenv import load_dotenv
load_dotenv()
lol: list[list[int]] = []

num_pixels = os.getenv("PIXELS")
num_pixels = 500

if num_pixels == None:
    raise Exception("No PIXELS env variable")

dirs = [0, 90, 180, 270]

points: list[Point] = []
for i in range(int(num_pixels)):
    print(f"generating point {i}", end="\r")
    points.append(Point(i, [
        f"scanning/results/results-{i}-0.png",
        f"scanning/results/results-{i}-90.png",
        f"scanning/results/results-{i}-180.png",
        f"scanning/results/results-{i}-270.png"
    ], [0, 90, 180, 270]))

centers: list[int] = []
for dir in dirs:
    temp: list[int] = []
    weights: list[float] = []
    for point in points:
        minVal, maxVal, minLoc, maxLoc = point.getPosForDir(dir)
        temp.append(maxLoc[1] * maxVal)
        weights.append(maxVal)
    centers.append(int(sum(temp) / sum(weights)))


for i, point in enumerate(points):

    # print(f"The brightest point in the image is at: {brightest_point}")
    # cv2.circle(img, maxLoc, 6, (255, 0, 0), 3)
    lol.append([point.getX(centers), point.getY(centers), point.getZ()])
    print(f"done {i}", end="\r")

    # cv2.imshow('image', img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

print(lol)
print(sum([x[0] for x in lol]) / 500)
print(sum([x[1] for x in lol]) / 500)
upload = input("upload to tree (y/n)")

if upload.lower() == "y":
    requests.post("http://192.168.1.50:5000/config/setlights", data=str(lol))
