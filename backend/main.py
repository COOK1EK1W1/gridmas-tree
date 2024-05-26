#!/usr/bin/python3

from util import tree
from webServer import app

from colors import Color
import threading

def wipe_on():
    for rng in range(0, int(tree.height * 200), 10):
        for i in range(len(tree.pixels)):
            if rng <= tree.coords[i][2] * 200 < rng + 10:
                tree.set_light(i, Color(200, 55, 2))
        tree.update()


if __name__ == '__main__':
    threading.Thread(target=app.run, kwargs={'debug': True, 'host':"0.0.0.0", "use_reloader":False, "port":3000}).start()
    tree.run()
