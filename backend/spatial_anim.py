import random
import time
import threading

import util


def xyz_planes(stopFlag: threading.Event):
    lol = util.read_csv()
    j = 1.1
    fps = 1/60
    rng = 10

    idk = 0
    while not stopFlag.is_set():
        idk = (idk + 1) % 3
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        for i in range(min(lol, key=lambda x: x[idk % 3])[idk % 3], max(lol, key=lambda x: x[idk % 3])[idk % 3], rng):
            for ia, light in enumerate(lol):
                if i <= light[idk % 3] < i + rng:
                    util.setLight(ia, color)
                else:
                    r, g, b = util.get_light(ia)
                    util.setLight(ia, (int(r/j), int(g/j), int(b/j)))
            util.update()
            time.sleep(fps)
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
