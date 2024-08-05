#!/usr/bin/python3

from tree import tree
import web_server

from dotenv import load_dotenv
import os


if __name__ == '__main__':
    load_dotenv()
    port = os.environ.get("PORT")
    if port is None:
        print("no PORT environment variable, trying 3000")
        port = 3000
    app = web_server.init()
    tree.run()
    app.run(debug=False, host="0.0.0.0", use_reloader=False, port=port)
