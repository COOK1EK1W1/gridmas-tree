import util
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
