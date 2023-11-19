import util
import random
import time
import threading


def doStandard(stopFlag: threading.Event):
    while not stopFlag.is_set():
        for i in range(util.pixel_num):
            util.setLight(i, (255, 255, 255))
            for ia in range(util.pixel_num):
                r, g, b = util.get_light(ia)
                util.setLight(ia, (int(r/1.1), int(g/1.1), int(b/1.1)))
            util.update()
            time.sleep(0.01)
            if (stopFlag.is_set()):
                break

def doTwinkle(stopFlag: threading.Event):
    while not stopFlag.is_set():
        x = random.randint(0, 499)
        util.setLight(x, (0, 100, 0))
        for ia in range(util.pixel_num):
            r, g, b = util.get_light(ia)
            color = (min(int(r+5), 100), min(int(g+5),255), min(20, int(b+5)))
            util.setLight(ia, color)
        util.update()
        time.sleep(0.02)
        if (stopFlag.is_set()):
            break
