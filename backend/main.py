#!/usr/bin/python3

from tree import tree
import web_server
import argparse


parser = argparse.ArgumentParser(description="")
parser.add_argument("--port", type=int, required=False, help="The port to host the Web Server")
parser.add_argument("--tree-file", type=str, required=False, help="specify the tree file")
parser.add_argument("--rate-limit", action="store_true", required=False, help="rate limit the web interface")

if __name__ == '__main__':
    args = parser.parse_args()

    # try load port from env
    port = args.port
    if port is None:
        port = 3000

    if args.rate_limit:
        app = web_server.init(True)
    else:
        app = web_server.init(False)

    tree.run()
    app.run(debug=False, host="0.0.0.0", use_reloader=False, port=int(port))
