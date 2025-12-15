from collections import defaultdict
import argparse
from typing import List, Optional
from cv2 import VideoCapture, imwrite, imshow, waitKey
import numpy as np

import cv2
from cv2.typing import MatLike
import requests
import time

print("init camera")

parser = argparse.ArgumentParser(description="Process num_light and url.")

# Add arguments with flags
parser.add_argument("--num-light", type=int, required=True, help="The number of lights")
parser.add_argument("--url", type=str, required=True, help="The URL to be processed")

# Parse the arguments
args = parser.parse_args()

light_amount = int(args.num_light)
url = "http://" + str(args.url)

cam_port = 0

cam_dir = 90
cam_flip = False


cam = VideoCapture(cam_port)

directions: list[tuple[int, list[Optional[tuple[float, float]]]]] = []


def get_img():
    a, image = cam.read()
    if cam_dir == 90:
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    return a, image


def get_photo_of(lights: list[list[int]]) -> MatLike:
    sent = False
    while not sent:
        x = requests.post(f"{url}/setalllight", data=str(lights))
        if x.status_code == 200:
            sent=True

    time.sleep(0.4)
    _, image = get_img()
    return image


def clear_tree():
    print("clearing light")
    sent = False
    while not sent:
        x = requests.get(url + "/lightoff")
        if x.status_code != 200:
            raise Exception("No Light Server")
        else:
            sent=True



def countdown(seconds: int):
    for i in range(seconds):
        print(seconds - i, end="\r")
        time.sleep(1)


dirs = [0, 90, 180, 270]


def loc_img2space(image: MatLike, loc: tuple[int, int]) -> tuple[float, float]:
    width = image.shape[1]
    height = image.shape[0]
    return ((loc[0] / width) * 2 - 1, (height / width) - (loc[1] / width))


def loc_space2img(image: MatLike, loc: tuple[float, float]) -> tuple[int, int]:
    width = image.shape[1]
    height = image.shape[0]
    newx = int(((loc[0] + 1) / 2) * width)
    newy = int((height - loc[1] * width))

    return (newx, newy)


def find_light_loc(image: MatLike):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, maxVal, _, maxLoc = cv2.minMaxLoc(gray)
    if maxVal > 100:
        return loc_img2space(image, (maxLoc[0], maxLoc[1]))
    else:
        return None


def find_light_loc_countour(image: MatLike) -> Optional[tuple[float, float]]:
    # Apply threshold to reduce noise
    _, thresholded = cv2.threshold(image, 30, 255, cv2.THRESH_BINARY)

    # Ensure the image is 8-bit single-channel for contour finding
    thresholded_8bit = thresholded.astype(np.uint8)

    # Find contours
    contours, _ = cv2.findContours(thresholded_8bit, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Find the largest contour
        largest_contour = max(contours, key=cv2.contourArea)

        # Calculate the centroid of the largest contour
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            return loc_img2space(image, (cx, cy))

    return None


def show_points(img: MatLike, points: list[Optional[tuple[float, float]]]):
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 0.5
    for i, point in enumerate(points):
        if point is not None:
            newx, newy = loc_space2img(img, (point[0], point[1]))
            print(newx, newy)
            cv2.putText(img, str(i), (newx + 5, newy - 5), font, fontScale, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.circle(img, (newx, newy), 6, (255, 0, 0), 3)
    cv2.imshow("test", img)
    waitKey(20)


def find_individual(pixels: list[int], revalidate_clean_plate: int = 5) -> list[Optional[tuple[float, float]]]:
    positions: list[Optional[tuple[float, float]]] = []
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


def find_lights(all_on: MatLike, all_off: MatLike, images: list[MatLike]) -> list[Optional[tuple[float, float]]]:
    all_on_subtracted = cv2.subtract(all_on, all_off)

    subtracted_images = list(map(lambda x: cv2.subtract(all_on, x), images))

    locations: list[Optional[tuple[float, float]]] = []

    for pixelid in range(light_amount):
        current_image = all_on_subtracted
        for i, image in enumerate(subtracted_images):
            if (pixelid & 0x1 << i) == 0:
                current_image = cv2.subtract(current_image, image)
            else:
                current_image = cv2.subtract(current_image, cv2.subtract(all_on_subtracted, image))

        locations.append(find_light_loc(current_image))
    return locations


def find_lights2(all_on: MatLike, all_off: MatLike, images: List[MatLike]) -> List[Optional[tuple[float, float]]]:
    all_on_gray = cv2.cvtColor(all_on, cv2.COLOR_BGR2GRAY) if len(all_on.shape) == 3 else all_on
    all_off_gray = cv2.cvtColor(all_off, cv2.COLOR_BGR2GRAY) if len(all_off.shape) == 3 else all_off
    images_gray = [cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img for img in images]

    all_on_subtracted = cv2.subtract(all_on_gray, all_off_gray)

    # Precompute subtracted images
    subtracted_images = [cv2.subtract(all_on_gray, img) for img in images_gray]

    # Calculate the number of bits (images)
    num_bits = len(images)

    # Precompute inverse subtracted images
    inverse_subtracted_images = [cv2.subtract(all_on_subtracted, img) for img in subtracted_images]

    locations: List[Optional[tuple[float, float]]] = []

    for pixelid in range(light_amount):
        current_image = all_on_subtracted.copy()

        for i in range(num_bits):
            if (pixelid & (1 << i)) == 0:
                current_image = cv2.subtract(current_image, subtracted_images[i])
            else:
                current_image = cv2.subtract(current_image, inverse_subtracted_images[i])

        locations.append(find_light_loc_countour(current_image))

        # Uncomment the following line if you want to visualize the process
        # show_points(current_image, [locations[-1]] if locations[-1] else [])

    return locations


def scan(dir: int):
    countdown(3)
    dir_degrees = dirs[int(dir) - 2]

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
    print(dir_degrees, locations)


def camera_test():
    requests.post(f"{url}/setalllight", data=str([[255, 255, 255] for _ in range(light_amount)]))
    while True:
        _, image = get_img()
        cv2.line(image, (image.shape[1] // 2, 0), (image.shape[1] // 2, image.shape[0]), (100, 0, 0), 2)
        imshow("test", image)
        key = waitKey(20)
        if key == 27:
            break


def combine_scans(scans: list[tuple[int, list[Optional[tuple[float, float]]]]]) -> list[tuple[float, float, float]]:
    # Accumulate observations for each light index
    observations: defaultdict[int, list[tuple[Optional[float], Optional[float], Optional[float]]]] = defaultdict(list)

    for direction, pixel_coords in scans:
        for light_index, point in enumerate(pixel_coords):
            if point is not None:
                # Determine the corresponding (X, Y, Z) based on the scan direction
                if direction == 0:
                    observations[light_index].append((point[0], point[1], None))  # Facing forward, Y is 0
                elif direction == 90:
                    observations[light_index].append((None, point[1], point[0]))  # Facing right, X is 0
                elif direction == 180:
                    observations[light_index].append((-point[0], point[1], None))  # Facing backward, negative X
                elif direction == 270:
                    observations[light_index].append((None, point[1], -point[0]))  # Facing left, negative Y
            else:
                observations[light_index].append((None, None, None))

    # Estimate 3D positions
    estimated_positions: list[tuple[float, float, float]] = []
    for light_index, data in observations.items():
        x_values: list[float] = []
        y_values: list[float] = []
        z_values: list[float] = []

        for (x, z, y) in data:
            if x is not None:
                x_values.append(x)
            if y is not None:
                y_values.append(y)
            if z is not None:
                z_values.append(z)
        print(x_values)

        avg_x = 0
        avg_y = 0
        avg_z = 0
        if len(x_values) > 0:
            avg_x = float(np.mean(x_values))
        if len(y_values) > 0:
            avg_y = float(np.mean(y_values))
        if len(z_values) > 0:
            avg_z = float(np.mean(z_values))

        estimated_positions.append((avg_x, avg_y, avg_z))

    return estimated_positions


def scale_locations_to_GIFT(locations: list[tuple[float, float, float]]):
    max_x = -1
    min_x = 1
    max_y = -1
    min_y = 1
    min_z = 100

    for location in locations:
        max_x = max(location[0], max_x)
        min_x = min(location[0], min_x)
        max_y = max(location[1], max_y)
        min_y = min(location[1], min_y)
        min_z = min(location[2], min_z)

    width = max_x - min_x
    depth = max_y - min_y

    scale_factor = 1

    if width > depth:
        scale_factor = 2 / width
    else:
        scale_factor = 2 / depth

    new_locations: list[tuple[float, float, float]] = []
    for location in locations:
        new_locations.append((float(location[0] * scale_factor), float(location[1] * scale_factor), float((location[2] - min_z) * scale_factor)))

    return new_locations


def fuse_data():
    new_locations = combine_scans(directions)
    lights: list[list[int]] = []
    for i in range(len(new_locations)):
        if new_locations[i][0] > 0:
            lights.append([255, 255, 255])
        else:
            lights.append([0, 0, 0])
    requests.post(f"{url}/setalllight", data=str(lights))
    res = input("ok? (y)")
    if res != "y":
        return
    scaled_locations = scale_locations_to_GIFT(new_locations)
    print("\n\n" + str(scaled_locations) + "\n\n")
    requests.post("http://172.10.20.4:5000/config/setlights", data=str(scaled_locations))

def run(option: int):
    if option == 1:
        camera_test()
    elif 1 < option < 6:
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

        locations = find_lights2(all_on, cleanimage, images)
        print(locations)
        show_points(all_on, locations)
        count = len(locations) - locations.count(None)
        print(f"locations found for {count} / {len(locations)}")
        directions.append((0, locations))

        locations = find_lights(all_on, cleanimage, images)
        show_points(all_on, locations)
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
        print(f"""
scanned directions {list(map(lambda x: x[0], directions))}
please select a function:
    1: camera test
    2: scan x+
    3: scan y+
    4: scan x-
    5: scan y-
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
