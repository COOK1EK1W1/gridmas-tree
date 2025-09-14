import time
import math
from gridmas import *

name = "Helix Spin"
author = "chatGPT"

# Constants for the HelixSpin pattern
ASCENT_SPEED = 0.01  # Speed of movement upwards
COLOR_CYCLE_SPEED = 0.05  # Speed of color change

angle_offset = 0  # Current angle offset for spinning
vertical_offset = 0  # Current vertical offset for moving upwards

HELIX_STRANDS = RangeAttr("helix strands", 1, 0, 4, 1)  # Number of strands in the helix
SPIN_SPEED = RangeAttr("spin speed", 0.08, 0.06, 0.24, 0.01)  # Speed of spinning around the tree
twist = RangeAttr("Twist", 6, 1, 20, 0.5)

def draw():
    global angle_offset, vertical_offset, HELIX_STRANDS, SPIN_SPEED, twist


    # Each frame, calculate the color based on a simple cycling pattern
    r = int((math.sin(COLOR_CYCLE_SPEED * seconds()) + 1) / 2 * 255)
    g = int((math.sin(COLOR_CYCLE_SPEED * seconds() + 2 * math.pi / 3) + 1) / 2 * 255)
    b = int((math.sin(COLOR_CYCLE_SPEED * seconds() + 4 * math.pi / 3) + 1) / 2 * 255)

    for pixel in tree.pixels:

        # Calculate the angle of this point around the center of the tree
        angle = math.atan2(pixel.y, pixel.x)
        # Determine the strand by position along the z-axis and the number of strands
        strand = int((HELIX_STRANDS.get() * (pixel.z / tree.height + vertical_offset)) % HELIX_STRANDS.get())

        # Check if the light is close to the helix for this strand
        if abs((angle - angle_offset - 2 * math.pi * strand / HELIX_STRANDS.get() + pixel.z * twist.get()) % (2 * math.pi) < 0.2 or (angle - angle_offset - 2 * math.pi * strand / HELIX_STRANDS.get() + pixel.z * twist.get()) % (2 * math.pi) > 2 * math.pi - 0.2):
            # Set the color for lights close to the helix part
            pixel.set_color(Color(r, g, b))
        else:
            # Dim other lights
            pixel.fade(1.1)


    # Move the helix
    angle_offset = (angle_offset + SPIN_SPEED.get()) % (2 * math.pi)
    vertical_offset = (vertical_offset + ASCENT_SPEED) % 1
