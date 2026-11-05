from tree import tree
from colors import Color
from attribute import RangeAttr
from attribute import ColorAttr
import math

name = "Barbershop Pole"
author = "Aiden Ruz"

# Barbershop Pole
def run():
    # Define the colors for the spiral stripes
    # Default RED
    col1 = ColorAttr("Color 1", Color(255, 0, 0))
    # Default WHITE
    col2 = ColorAttr("Color 2", Color(255, 255, 255))
    # Default BLUE
    col3 = ColorAttr("Color 3", Color(0, 0, 255))
    colors = [col2.get(), col3.get(), col2.get(), col1.get()]  # Four stripes in sequence
    
    # Stripe and motion configuration
    num_stripes = 8  # Increase number of stripes for smaller and more frequent ones
    stripe_height = tree.height / num_stripes  # Height of each stripe
    speed = RangeAttr("Speed", 0.02, 0.001, 0.05, 0.001)

    rotations = 8  # Amount of full rotations to make the spiral tighter or looser
    spiral_twist = (2 * math.pi * rotations) / tree.height  # Calculates twist of the spiral for tightness

    offset = 0  # Offset for upward motion

    while True:
        # Colors reassigned in loop to ensure that they can be changed
        colors = [col2.get(), col3.get(), col2.get(), col1.get()]  # Four stripes in sequence
        offset += speed.get()  # Move the spiral upward
        for pixel in tree.pixels:
            # Calculate angle around the z-axis (cylindrical coordinates)
            angle = math.atan2(pixel.y, pixel.x)

            # Combine angle and upward motion to determine stripe
            relative_z = (pixel.z - offset) - (angle / spiral_twist) * stripe_height
            stripe_index = int(relative_z // stripe_height) % len(colors)

            # Assign color based on the stripe index
            pixel.lerp(colors[stripe_index].to_tuple(), 5)

        # Update the tree to display changes
        tree.update()
