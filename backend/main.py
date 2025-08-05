#!/usr/bin/python3

from renderer import Renderer
from pattern_manager import PatternManager
from tree import tree
from pattern_manager import PatternManager
import web_server
import argparse
import multiprocessing


parser = argparse.ArgumentParser(description="")
parser.add_argument("--port", type=int, required=False, help="The port to host the Web Server")
parser.add_argument("--tree-file", type=str, required=False, help="specify the tree file")
parser.add_argument("--rate-limit", action="store_true", required=False, help="rate limit the web interface")
parser.add_argument("--pattern-dir", type=str, required=False, help="the directory containing patterns")

if __name__ == '__main__':
    args = parser.parse_args()

    # try load port from env
    port = args.port
    if port is None:
        port = 3000

    is_rate_limit = False
    if args.rate_limit:
        is_rate_limit = True

    patternManager = PatternManager(args.pattern_dir or "patterns/")

    tree.init(args.tree_file or "tree.csv")

    renderer = Renderer(tree.coords)

    app = web_server.init(is_rate_limit, patternManager)
    multiprocessing.Process(target=app.run, kwargs={"debug":False, "host":"0.0.0.0", "use_reloader":False, "port":int(port)}).start()

    while True:

        # 1 handle web request queue
        patternManager.handle_queue()

        # 2. call draw()
        patternManager.draw_current()

        # 3. get pixels from tree instance
        frame = tree.request_frame()

        # 4. send to pixel driver | blocks until space
        renderer.add_to_queue(frame)
