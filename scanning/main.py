from cv2 import VideoCapture, imwrite, imshow, waitKey, destroyAllWindows
import math

import cv2
from cv2.typing import MatLike, Point
import requests
import time

print("init camera")

cam_port = 0

url = "http://192.168.1.249"

light_amount = 350




cam = VideoCapture(cam_port)

directions: list[tuple[int, list[Point | None]]] = []


def get_photo_of(lights: list[list[int]]) -> MatLike:
    requests.post(f"{url}/setalllight", data=str(lights))

    time.sleep(0.2)
    result, image = cam.read()
    time.sleep(0.2)
    return image


def clear_tree():
    print("clearing light")
    x = requests.get(url + "/lightoff")
    if x.status_code != 200:
        raise Exception("No Light Server")


def countdown(seconds: int):
    for i in range(seconds):
        print(seconds - i, end="\r")
        time.sleep(1)


dirs = [0, 90, 180, 270]


def find_light_loc(image: MatLike):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(gray)
    if maxVal > 100:
        return maxLoc
    else:
        return None


def find_lights(all_on: MatLike, all_off: MatLike, images: list[MatLike]) -> list[Point | None]:
    all_on_subtracted = cv2.subtract(all_on, all_off)

    subtracted_images = list(map(lambda x: cv2.subtract(all_on, x), images))

    locations: list[Point | None] = []

    for pixelid in range(light_amount):
        current_image = all_on_subtracted
        for i, image in enumerate(subtracted_images):
            if (pixelid & 0x1 << i) == 0:
                current_image = cv2.subtract(current_image, image)
            else:
                current_image = cv2.subtract(current_image, cv2.subtract(all_on_subtracted, image))

        locations.append(find_light_loc(current_image))
    return locations


def show_points(img: MatLike, points: list[Point | None]):
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 0.5
    for i, point in enumerate(points):
        if point is not None:
            cv2.putText(img, str(i), point, font, fontScale, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.circle(img, point, 6, (255, 0, 0), 3)
    cv2.imshow("test", img)
    waitKey(20)


def find_individual(pixels: list[int], revalidate_clean_plate: int = 5) -> list[Point | None]:
    positions: list[Point | None] = []
    clear_tree()
    colors = [[0, 0, 0] for _ in range(light_amount)]
    clean_plate = get_photo_of(colors)
    i = 0
    for pixel in pixels:
        if i % revalidate_clean_plate == 0:
            colors = [[0, 0, 0] for _ in range(light_amount)]
            clean_plate = get_photo_of(colors)
        print(f"finding {i}", end="\r")
        colors = [[0, 0, 0] for _ in range(light_amount)]
        colors[pixel] = [255, 255, 255]
        new_photo = get_photo_of(colors)
        isolated = cv2.subtract(new_photo, clean_plate)
        positions.append(find_light_loc(isolated))
        i += 1
    return positions


def scan(dir: int):
    countdown(3)
    dir_degrees = dirs[int(dir) - 1]

    # get all lights on
    all_on = get_photo_of([[255, 255, 255] for _ in range(light_amount)])
    print("on")
    imwrite(f"results/results2-on-{dir_degrees}.png", all_on)

    # get all lights off
    all_off = get_photo_of([[0, 0, 0] for _ in range(light_amount)])
    print("off")
    imwrite(f"results/results2-off-{dir_degrees}.png", all_off)

    images: list[MatLike] = []

    for a in range(light_amount.bit_length()):
        colors: list[list[int]] = []
        for x in range(light_amount):
            if x & (1 << a) != 0:
                colors.append([0, 0, 0])
            else:
                colors.append([255, 255, 255])

        image = get_photo_of(colors)
        images.append(image)
        print(1 << a)
        imwrite(f"results/results2-{a}-{dir_degrees}.png", image)

    locations = find_lights(all_on, all_off, images)

    show_points(all_on, locations)

    count = len(locations) - locations.count(None)
    print(f"locations found for {count} / {len(locations)}")

    none_positions = [index for index, location in enumerate(locations) if location is None]

    fixed_positions = find_individual(none_positions)
    for i, position in enumerate(none_positions):
        locations[position] = fixed_positions[i]

    count = len(locations) - locations.count(None)
    print(f"locations found for {count} / {len(locations)}")

    show_points(all_on, locations)

    directions.append((dir_degrees, locations))


def camera_test():
    while True:
        result, image = cam.read()
        cv2.line(image, (image.shape[1] // 2, 0), (image.shape[1] // 2, image.shape[0]), (100, 0, 0), 2)
        imshow("test", image)
        key = waitKey(20)
        if key == 27:
            break


def fuse_data():
    for direction in directions:
        angle = direction[0]
        locations = direction[1]
        math.cos(angle / 180 * math.pi)


def run(option: int):
    if option == 5:
        camera_test()
    elif 0 < option < 5:
        scan(option)
    elif option == 6:

        imagedirs = [
            "results/results2-0-0.png",
            "results/results2-1-0.png",
            "results/results2-2-0.png",
            "results/results2-3-0.png",
            "results/results2-4-0.png",
            "results/results2-5-0.png",
            "results/results2-6-0.png",
            "results/results2-7-0.png",
            "results/results2-8-0.png",
        ]

        cleanplate = "results/results2-off-0.png"
        cleanimage = cv2.imread(cleanplate)

        all_on = cv2.imread("results/results2-on-0.png")
        images = list(map(lambda x: cv2.imread(x), imagedirs))
        locations = find_lights(all_on, cleanimage, images)
        for location in locations:
            if location is not None:
                cv2.circle(all_on, location, 6, (255, 0, 0), 3)
        cv2.imshow("test", all_on)
        print(locations)
        count = len(locations) - locations.count(None)
        print(f"locations found for {count} / {len(locations)}")
        waitKey(20)
    elif option == 7:
        countdown(2)
        all_on = get_photo_of([[255, 255, 255] for _ in range(light_amount)])
        all_off = get_photo_of([[0, 0, 0] for _ in range(light_amount)])
        imshow("test", cv2.subtract(all_on, all_off))
        waitKey(20)
    elif option == 8:
        fuse_data()


if __name__ == "__main__":
    while True:
        clear_tree()
        print("""please select a function:
    1: scan x+
    2: scan y+
    3: scan x-
    4: scan y-
    5: camera test
    6: pixel find test
    7: difference test
    8: fuse data + send""")
        option = input("choose:")
        try:
            if not int(option):
                continue

            run(int(option))

        except Exception as err:
            print(err)
