from attribute import RangeAttr
from colors import Color
from tree import tree
import time
import math
import os





name = "Christmas Helix Tree"
author = "Aadham Ahmad"


def run():
    SECTORS = RangeAttr("Number of Sectors - each sector has 2 helixes", 2, 1, 4, 1)
    TWIST_ANGLE = RangeAttr("Twist Angle of Helixes - higher means straighter, 0 equals perfectly straight ", 2.5, -4, 4, 0.1)
    SPIN_SPEED = RangeAttr("Speed of Rotation - how fast the helixes spin", 2, 1, 20, 1)
    STAR_BEGIN = RangeAttr("Star Height - what height (%) to begin star at", 0.85, 0.7, 1, 0.01)
    COLOUR_OR_DIM = RangeAttr("Colour or Dim Smoothing - 0 means colour, 1 means dimming", 1, 0, 1, 1)
    SMOOTHING = RangeAttr("Smoothing Factor - lower means smoother", 1.2, 0.1, 2, 0.1)

    XMAS_GREEN = [60,200,13]
    XMAS_RED = [211,19,19]
    GOLD = [255,215,0]
    MID_COLOR = [abs(red - green) 
                 for red in XMAS_RED 
                 for green in XMAS_GREEN]
    
    START_TIME = time.time()
    TWO_PI = 2 * math.pi

    while True:
        # Range variables
        star_height = tree.height * STAR_BEGIN.get()
        sector_width = (TWO_PI) / SECTORS.get()
        smooth_factor = SMOOTHING.get()
        twist_rate = TWIST_ANGLE.get()
        dimming = COLOUR_OR_DIM.get()
        speed = SPIN_SPEED.get()
        
        # Other variables
        quadrant = sector_width / 4
        angle_offset = speed * (time.time() - START_TIME)

        for pixel in tree.pixels:
            # Is a star pixel so set to gold
            if pixel.z >= star_height:
                pixel.set_color(Color(GOLD[0], GOLD[1], GOLD[2]))
                continue

            # Rotation values for twist angle of helix
            twist_position = ((pixel.z / twist_rate) % 1) if twist_rate != 0 else 0
            rotation_angle = twist_position * TWO_PI + angle_offset

            # Radian calculations adjusted for rotation & normalization
            radian_angle = math.atan2(pixel.y, pixel.x)
            normalized_angle = (radian_angle + TWO_PI) % (TWO_PI)
            rotated_angle = normalized_angle + rotation_angle
            rotated_angle = (rotated_angle + TWO_PI) % TWO_PI

            # Determine the sector and helix index
            sector_index = int(normalized_angle // sector_width)
            helix_index = int((rotated_angle // (sector_width/2)) % 2)
            colour = XMAS_RED if helix_index == 0 else XMAS_GREEN

            # Center angle calculations for smoothing
            sector_center = sector_index * sector_width + (sector_width / 2)
            helix_center = sector_center + (quadrant if helix_index == 0 else (-quadrant))
            distance = abs(helix_center - normalized_angle)

            # Final smoothing calculations
            gaussian_curve = 1 * math.exp(-(distance ** 2) / (2 * smooth_factor ** 2))
            if dimming: colour = [int(rgb * gaussian_curve) for rgb in colour]
            else: colour = [int((rgb*gaussian_curve) + (MID_COLOR[i] * (1-gaussian_curve))) for i, rgb in enumerate(colour)]

            # Set pixel colour to appropriate value
            pixel.set_color(Color(colour[0], colour[1], colour[2]))
            
        # Update the tree display
        tree.update()
