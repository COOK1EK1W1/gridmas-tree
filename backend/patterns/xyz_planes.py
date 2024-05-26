from colors import Color
from tree import tree

name = "XYZ Planes"
author = "Ciaran"


def run():
    j = 1.1
    rng = 10

    idk = 0
    while True:
        idk = (idk + 1) % 3
        color = Color.random()
        for i in range(-200, 200, rng):
            for ia, coord in enumerate(tree.coords):
                if i <= (coord[idk % 3] * 200) < i + rng:
                    tree.set_light(ia, color)
                else:
                    tree.get_light(ia).fade()
            tree.update()

        idk = (idk + 1) % 3
        color = Color.random()
        for i in range(0, int(tree.height * 200), rng):
            for ia, light in enumerate(tree.coords):
                if i <= (light[idk % 3] * 200) < i + rng:
                    tree.set_light(ia, color)
                else:
                    tree.get_light(ia).fade(j)
            tree.update()

        idk = (idk + 1) % 3
        color = Color.random()
        for i in range(-200, 200, rng):
            for ia, coord in enumerate(tree.coords):
                if i <= (coord[idk % 3] * 200) < i + rng:
                    tree.set_light(ia, color)
                else:
                    tree.get_light(ia).fade(j)
            tree.update()
