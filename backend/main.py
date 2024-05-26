#!/usr/bin/python3

from util import tree
from webServer import app
import threading

if __name__ == '__main__':
    threading.Thread(target=app.run, kwargs={'debug': True, 'host':"0.0.0.0", "use_reloader":False, "port":3000}).start()
    tree.run()
