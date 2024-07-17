#!/usr/bin/python3

from tree import tree
from webServer import app
import threading

from dotenv import load_dotenv
import os


if __name__ == '__main__':
    load_dotenv()
    port = os.environ.get("PORT")
    if port is None:
        print("no PORT environment variable, trying 3000")
        port = 3000
    threading.Thread(target=app.run, kwargs={'debug': True, 'host': "0.0.0.0", "use_reloader": False, "port": port}).start()
    tree.run()
