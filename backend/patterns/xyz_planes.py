import random
import time

from util import tree
def xyz_planes():
    j = 1.1
    fps = 1/60
    rng = 10

    idk = 0
    while True:
        idk = (idk + 1) % 3
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        for i in range(-200, 200, rng):
            for ia, coord in enumerate(tree.coords):
                if i <= (coord[idk % 3] * 200) < i + rng:
                    tree.set_light(ia, color)
                else:
                    r, g, b = tree.get_light(ia)
                    tree.set_light(ia, (int(r/j), int(g/j), int(b/j)))
            tree.update()
            time.sleep(fps)

        idk = (idk + 1) % 3
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        for i in range(0, int(tree.height*200), rng):
            for ia, light in enumerate(tree.coords):
                if i <= (light[idk % 3] * 200) < i + rng:
                    tree.set_light(ia, color)
                else:
                    r, g, b = tree.get_light(ia)
                    tree.set_light(ia, (int(r/j), int(g/j), int(b/j)))
            tree.update()
            time.sleep(fps)

        idk = (idk + 1) % 3
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        for i in range(-200, 200, rng):
            for ia, coord in enumerate(tree.coords):
                if i <= (coord[idk % 3] * 200) < i + rng:
                    tree.set_light(ia, color)
                else:
                    r, g, b = tree.get_light(ia)
                    tree.set_light(ia, (int(r/j), int(g/j), int(b/j)))
            tree.update()
            time.sleep(fps)


