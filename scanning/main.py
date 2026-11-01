from collections import defaultdict
import argparse
from typing import Optional
from cv2 import VideoCapture, imwrite, imshow, waitKey
import numpy as np

import cv2
from cv2.typing import MatLike
import requests
import sys
import termios
import time
import tty
from pathlib import Path

# append, not insert: backend/main.py must not shadow this file
sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))
from network_driver import NetworkPixelDriver

from decode import decode_lights, find_suspects, gray_encode, num_bits
from postprocess import PartialPosition, clean_positions, scale_locations_to_GIFT

print("init camera")

parser = argparse.ArgumentParser(description="Process num_light and url.")

# Add arguments with flags
parser.add_argument("--num-light", type=int, required=True, help="The number of lights")
parser.add_argument("--url", type=str, required=True, help="The device to scan, as host or host:port")
parser.add_argument("--outlier-percent", type=float, default=2, help="The percent of LEDs furthest out of line with their neighbours to interpolate, 0 for none")

# Parse the arguments
args = parser.parse_args()

light_amount = int(args.num_light)
address, _, device_port = str(args.url).partition(":")

cam_port = 0

cam_dir = 0
cam_flip = False


cam = VideoCapture(cam_port)

# a changing exposure breaks comparing one photo against another, but backends
# differ in the value they want and some (macOS) ignore this altogether
if not cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25):
    print("warning: could not lock camera exposure")
cam.set(cv2.CAP_PROP_AUTO_WB, 0)

directions: list[tuple[int, list[Optional[tuple[float, float]]]]] = []

# scanning has nothing to keep in sync, so frames only lead by enough to arrive on time
DISPLAY_LEAD_S = 0.2
FRAME_RETRY_S = 0.5
# in scan space, where the image is 2 wide
MAX_HEIGHT_SPREAD = 0.1
# frames sat in the camera's buffer from before the lights changed
STALE_CAMERA_FRAMES = 5
KEY_LEFT = "\x1b[D"
KEY_RIGHT = "\x1b[C"

driver = NetworkPixelDriver(address, 1000, "scanner", port=int(device_port or NetworkPixelDriver.DEFAULT_PORT))


def show_lights(lights: list[list[int]]):
    """Put a frame on the device, blocking until its display time has passed.

    The driver drops a frame that goes stale waiting on a connection, which
    is fine for a pattern but not here, so keep trying until one is sent.
    """
    driver.pixel_buffer[:offset+light_amount] = lights
    sent_before = driver.stats()["sent"]
    while True:
        display_at = time.time() + DISPLAY_LEAD_S
        driver.flush(display_at)
        deadline = time.time() + FRAME_RETRY_S
        while time.time() < deadline:
            if driver.stats()["sent"] > sent_before:
                time.sleep(max(0, display_at - time.time()))
                return
            time.sleep(0.005)


def get_img():
    a, image = cam.read()
    if cam_dir == 90:
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    return a, image


def get_photo_of(lights: list[list[int]]) -> MatLike:
    show_lights(lights)
    time.sleep(0.4)
    for _ in range(STALE_CAMERA_FRAMES):
        cam.grab()
    _, image = get_img()
    return image


def clear_tree():
    print("clearing light")
    show_lights([[0, 0, 0] for _ in range(light_amount)])



def countdown(seconds: int):
    for i in range(seconds):
        print(seconds - i, end="\r")
        time.sleep(1)


dirs = [0, 90, 180, 270]


def loc_img2space(image: MatLike, loc: tuple[float, float]) -> tuple[float, float]:
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


def gray_pattern(bit: int, inverted: bool) -> list[list[int]]:
    """Light every LED whose gray code has this bit set, or clear if inverted"""
    colors: list[list[int]] = []
    for x in range(light_amount):
        if bool(gray_encode(x) & (1 << bit)) != inverted:
            colors.append([255, 255, 255])
        else:
            colors.append([0, 0, 0])
    return colors


def find_lights(all_on: MatLike, positives: list[MatLike], negatives: list[MatLike]) -> tuple[list[Optional[tuple[float, float]]], list[int]]:
    """Decode the photos into a location per LED, and the LEDs not to trust."""
    decoded = decode_lights(
        [cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) for image in positives],
        [cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) for image in negatives],
        light_amount,
    )
    locations: list[Optional[tuple[float, float]]] = []
    for light in decoded:
        locations.append(None if light is None else loc_img2space(all_on, (light[0], light[1])))
    return locations, find_suspects(decoded)


def scan(dir: int):
    countdown(3)
    dir_degrees = dirs[int(dir) - 2]
    Path("results").mkdir(exist_ok=True)

    # only used to draw the results on
    all_on = get_photo_of([[255, 255, 255] for _ in range(light_amount)])
    print("on")
    imwrite(f"results/results3-on-{dir_degrees}.png", all_on)

    positives: list[MatLike] = []
    negatives: list[MatLike] = []

    for a in range(num_bits(light_amount)):
        positives.append(get_photo_of(gray_pattern(a, False)))
        negatives.append(get_photo_of(gray_pattern(a, True)))
        print(1 << a)
        imwrite(f"results/results3-{a}-pos-{dir_degrees}.png", positives[-1])
        imwrite(f"results/results3-{a}-neg-{dir_degrees}.png", negatives[-1])

    locations, suspects = find_lights(all_on, positives, negatives)

    show_points(all_on, locations)

    count = len(locations) - locations.count(None)
    print(f"locations found for {count} / {len(locations)}, {len(suspects)} suspect")

    rescan_positions = sorted(suspects + [index for index, location in enumerate(locations) if location is None])

    fixed_positions = find_individual(rescan_positions)
    for i, position in enumerate(rescan_positions):
        locations[position] = fixed_positions[i]

    count = len(locations) - locations.count(None)
    print(f"locations found for {count} / {len(locations)}")

    show_points(all_on, locations)

    directions.append((dir_degrees, locations))
    print(dir_degrees, locations)


def camera_test():
    show_lights([[255, 255, 255] for _ in range(light_amount)])
    while True:
        _, image = get_img()
        cv2.line(image, (image.shape[1] // 2, 0), (image.shape[1] // 2, image.shape[0]), (100, 0, 0), 2)
        imshow("test", image)
        key = waitKey(20)
        if key == 27:
            break


def read_key() -> str:
    key = sys.stdin.read(1)
    if key == "\x1b":  # arrow keys arrive as a three character escape sequence
        key += sys.stdin.read(2)
    return key


def step_lights():
    """Light one LED at a time, moved with the left and right arrow keys."""
    print("left/right: move, q: back to menu")
    stdin_fd = sys.stdin.fileno()
    terminal_settings = termios.tcgetattr(stdin_fd)
    tty.setcbreak(stdin_fd)
    light = 0
    try:
        while True:
            colors = [[0, 0, 0] for _ in range(light_amount)]
            colors[light] = [255, 255, 255]
            show_lights(colors)
            print(f"led {light} / {light_amount - 1}    ", end="\r", flush=True)

            key = read_key()
            if key == KEY_LEFT:
                light = (light - 1) % light_amount
            elif key == KEY_RIGHT:
                light = (light + 1) % light_amount
            elif key == "q":
                break
    finally:
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, terminal_settings)
        print()


def combine_scans(scans: list[tuple[int, list[Optional[tuple[float, float]]]]]) -> list[PartialPosition]:
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
    estimated_positions: list[PartialPosition] = []
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

        # every view measures height, so one bad view shows up here and the median ignores it
        if len(z_values) > 1 and max(z_values) - min(z_values) > MAX_HEIGHT_SPREAD:
            print(f"warning: views disagree on the height of led {light_index}: {z_values}")

        avg_x = None
        avg_y = None
        avg_z = None
        if len(x_values) > 0:
            avg_x = float(np.mean(x_values))
        if len(y_values) > 0:
            avg_y = float(np.mean(y_values))
        if len(z_values) > 0:
            avg_z = float(np.median(z_values))

        estimated_positions.append((avg_x, avg_y, avg_z))

    return estimated_positions


def fuse_data():
    new_locations, outliers = clean_positions(combine_scans(directions), args.outlier_percent)
    print(f"interpolated outliers: {outliers}")
    lights: list[list[int]] = []
    for i in range(len(new_locations)):
        if new_locations[i][0] > 0:
            lights.append([255, 255, 255])
        else:
            lights.append([0, 0, 0])
    show_lights(lights)
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

        bits = range(num_bits(light_amount))
        all_on = cv2.imread("results/results3-on-0.png")
        positives = [cv2.imread(f"results/results3-{a}-pos-0.png") for a in bits]
        negatives = [cv2.imread(f"results/results3-{a}-neg-0.png") for a in bits]

        locations, suspects = find_lights(all_on, positives, negatives)
        print(locations)
        show_points(all_on, locations)
        count = len(locations) - locations.count(None)
        print(f"locations found for {count} / {len(locations)}, suspect: {suspects}")
        directions.append((0, locations))
        waitKey(20)
    elif option == 7:
        countdown(2)
        all_on = get_photo_of([[255, 255, 255] for _ in range(light_amount)])
        all_off = get_photo_of([[0, 0, 0] for _ in range(light_amount)])
        imshow("test", cv2.subtract(all_on, all_off))
        waitKey(20)
    elif option == 8:
        fuse_data()
    elif option == 9:
        step_lights()


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
    8: fuse data + send
    9: step through leds""")
        option = input("choose:")
        try:
            if not int(option):
                continue

            run(int(option))

        except Exception as err:
            print(err)
