import time
import math
from attribute import RangeAttr
from util import tree
from colors import Color

name = "HelixSpin"
display_name = "Helix Spin"
author = "chatGPT"

# Constants for the HelixSpin pattern
ASCENT_SPEED = 0.01  # Speed of movement upwards
COLOR_CYCLE_SPEED = 0.05  # Speed of color change


def run():
    angle_offset = 0  # Current angle offset for spinning
    vertical_offset = 0  # Current vertical offset for moving upwards

    HELIX_STRANDS = RangeAttr("helix strands", 1, 0, 4, 1)  # Number of strands in the helix
    SPIN_SPEED = RangeAttr("spin speed", 0.08, 0.06, 0.24, 0.01)  # Speed of spinning around the tree
    twist = RangeAttr("Twist", 6, 1, 20, 0.5)

    while True:
        # Each frame, calculate the color based on a simple cycling pattern
        r = int((math.sin(COLOR_CYCLE_SPEED * time.time()) + 1) / 2 * 255)
        g = int((math.sin(COLOR_CYCLE_SPEED * time.time() + 2 * math.pi / 3) + 1) / 2 * 255)
        b = int((math.sin(COLOR_CYCLE_SPEED * time.time() + 4 * math.pi / 3) + 1) / 2 * 255)

        for i, coord in enumerate(tree.coords):
            x, y, z = coord

            # Calculate the angle of this point around the center of the tree
            angle = math.atan2(y, x)
            # Determine the strand by position along the z-axis and the number of strands
            strand = int((HELIX_STRANDS.get() * (z / tree.height + vertical_offset)) % HELIX_STRANDS.get())

            # Check if the light is close to the helix for this strand
            if abs((angle - angle_offset - 2 * math.pi * strand / HELIX_STRANDS.get() + z * twist.get()) % (2 * math.pi) < 0.2 or (angle - angle_offset - 2 * math.pi * strand / HELIX_STRANDS.get() + z * twist.get()) % (2 * math.pi) > 2 * math.pi - 0.2):
                # Set the color for lights close to the helix part
                tree.set_light(i, Color(r, g, b))
            else:
                # Dim other lights
                tree.set_light(i, Color.black())

        # Update the tree display
        tree.update()

        # Move the helix
        angle_offset = (angle_offset + SPIN_SPEED.get()) % (2 * math.pi)
        vertical_offset = (vertical_offset + ASCENT_SPEED) % 1

        # Control the update speed to make the animation smooth
        time.sleep(1 / 30)  # Aiming for around 30 frames per second
