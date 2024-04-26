from colors import Color
import time
from util import tree

name = "xyz_planes"
display_name = "xyz Planes"


def run():
    j = 1.1
    fps = 1 / 60
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
                    r, g, b = tree.get_light(ia)
                    tree.set_light(ia, Color(int(r / j), int(g / j), int(b / j)))
            tree.update()
            time.sleep(fps)

        idk = (idk + 1) % 3
        color = Color.random()
        for i in range(0, int(tree.height * 200), rng):
            for ia, light in enumerate(tree.coords):
                if i <= (light[idk % 3] * 200) < i + rng:
                    tree.set_light(ia, color)
                else:
                    r, g, b = tree.get_light(ia)
                    tree.set_light(ia, Color(int(r / j), int(g / j), int(b / j)))
            tree.update()
            time.sleep(fps)

        idk = (idk + 1) % 3
        color = Color.random()
        for i in range(-200, 200, rng):
            for ia, coord in enumerate(tree.coords):
                if i <= (coord[idk % 3] * 200) < i + rng:
                    tree.set_light(ia, color)
                else:
                    r, g, b = tree.get_light(ia)
                    tree.set_light(ia, Color(int(r / j), int(g / j), int(b / j)))
            tree.update()
            time.sleep(fps)
