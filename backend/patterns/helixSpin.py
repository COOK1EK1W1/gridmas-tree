import time
import math

from util import tree

# Constants for the HelixSpin pattern
HELIX_STRANDS = 1  # Number of strands in the helix
SPIN_SPEED = 0.08  # Speed of spinning around the tree
ASCENT_SPEED = 0.01  # Speed of movement upwards
COLOR_CYCLE_SPEED = 0.05  # Speed of color change
twist = 6

name = "HelixSpin"
display_name = "Helix Spin"
author = "chatGPT"

def run():
    angle_offset = 0  # Current angle offset for spinning
    vertical_offset = 0  # Current vertical offset for moving upwards

    while True:
        # Each frame, calculate the color based on a simple cycling pattern
        r = int((math.sin(COLOR_CYCLE_SPEED * time.time()) + 1) / 2 * 255)
        g = int((math.sin(COLOR_CYCLE_SPEED * time.time() + 2 * math.pi / 3) + 1) / 2 * 255)
        b = int((math.sin(COLOR_CYCLE_SPEED * time.time() + 4 * math.pi / 3) + 1) / 2 * 255)
        spiral_color = (r, g, b)

        for i, coord in enumerate(tree.coords):
            x, y, z = coord

            # Calculate the angle of this point around the center of the tree
            angle = math.atan2(y, x)
            # Determine the strand by position along the z-axis and the number of strands
            strand = int((HELIX_STRANDS * (z / tree.height + vertical_offset)) % HELIX_STRANDS)

            # Check if the light is close to the helix for this strand
            if abs((angle - angle_offset - 2 * math.pi * strand / HELIX_STRANDS +z*twist) % (2 * math.pi) < 0.2 or
                    (angle - angle_offset - 2 * math.pi * strand / HELIX_STRANDS + z*twist) % (2 * math.pi) > 2 * math.pi - 0.2):
                # Set the color for lights close to the helix part
                tree.set_light(i, spiral_color)
            else:
                # Dim other lights
                tree.set_light(i, (0, 0, 0))

        # Update the tree display
        tree.update()

        # Move the helix
        angle_offset = (angle_offset + SPIN_SPEED) % (2 * math.pi)
        vertical_offset = (vertical_offset + ASCENT_SPEED) % 1

        # Control the update speed to make the animation smooth
        time.sleep(1/30)  # Aiming for around 30 frames per second
