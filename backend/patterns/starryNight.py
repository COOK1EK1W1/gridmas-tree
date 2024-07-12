import random
import math
from attribute import RangeAttr, ColorAttr
from tree import tree
from colors import Color

name = "Starry Night"
author = "Claude"


class Star:
    def __init__(self, index, brightness):
        self.index = index
        self.brightness = brightness
        self.twinkle_speed = random.uniform(0.02, 0.1)
        self.twinkle_offset = random.uniform(0, 2 * math.pi)


class ShootingStar:
    def __init__(self, start_index, direction, speed):
        self.current_index = start_index
        self.direction = direction
        self.speed = speed
        self.life = 1.0


def run():
    star_density = RangeAttr("Star Density", 0.1, 0.05, 0.3, 0.01)
    shooting_star_chance = RangeAttr("Shooting Star Chance", 0.01, 0.001, 0.05, 0.001)

    background_color = Color(0, 0, 0)  # Dark blue night sky
    star_color = ColorAttr("Star Color", Color(255, 255, 200))  # Warm white

    stars = []
    shooting_stars = []
    time = 0

    # Initialize stars
    for i in range(tree.num_pixels):
        if random.random() < star_density.get():
            stars.append(Star(i, random.uniform(0.1, 1.0)))

    while True:
        # Clear the tree
        for i in range(tree.num_pixels):
            tree.set_light(i, background_color)

        # Update and draw stars
        for star in stars:
            brightness = star.brightness * (0.5 + 0.5 * math.sin(time * star.twinkle_speed + star.twinkle_offset))
            color = Color(
                int(star_color.get().r * brightness),
                int(star_color.get().g * brightness),
                int(star_color.get().b * brightness)
            )
            tree.set_light(star.index, color)

        # Update and draw shooting stars
        for shooting_star in shooting_stars:
            color = Color(
                int(star_color.get().r * shooting_star.life),
                int(star_color.get().g * shooting_star.life),
                int(star_color.get().b * shooting_star.life)
            )
            tree.set_light(int(shooting_star.current_index), color)

            # Move the shooting star
            shooting_star.current_index += shooting_star.speed * shooting_star.direction
            shooting_star.life -= 0.05

        # Remove dead shooting stars
        shooting_stars = [ss for ss in shooting_stars if ss.life > 0]

        # Chance to add a new shooting star
        if random.random() < shooting_star_chance.get():
            start_index = random.randint(0, tree.num_pixels - 1)
            direction = 1 if random.random() < 0.5 else -1
            speed = random.uniform(0.5, 2.0)
            shooting_stars.append(ShootingStar(start_index, direction, speed))

        tree.update()
        time += 0.1

        # Occasionally add or remove stars
        if random.random() < 0.01:
            if random.random() < 0.5 and len(stars) > 0:
                stars.pop(random.randint(0, len(stars) - 1))
            elif len(stars) < tree.num_pixels * star_density.get():
                new_index = random.randint(0, tree.num_pixels - 1)
                if new_index not in [star.index for star in stars]:
                    stars.append(Star(new_index, random.uniform(0.1, 1.0)))
