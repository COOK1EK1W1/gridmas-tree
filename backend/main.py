#!/usr/bin/python3

from renderer import Renderer
from pattern_manager import PatternManager
from tree import tree
from pattern_manager import PatternManager
from web_server import DrawFrame, StartPattern, StopPattern, WebServer
import argparse

# add the command line arguments
parser = argparse.ArgumentParser(description="")
parser.add_argument("--port", type=int, required=False, help="The port to host the Web Server")
parser.add_argument("--tree-file", type=str, required=False, help="specify the tree file")
parser.add_argument("--rate-limit", action="store_true", required=False, help="rate limit the web interface")
parser.add_argument("--pattern-dir", type=str, required=False, help="the directory containing patterns")

if __name__ == '__main__':
    args = parser.parse_args()

    # Start pattern manager and load patterns
    patternManager = PatternManager(args.pattern_dir or "patterns/")

    # initialise tree
    tree.init(args.tree_file or "tree.csv")

    # Initialise the rendering pipeline
    renderer = Renderer(tree.coords)

    # Web server
    is_rate_limit = False
    if args.rate_limit:
        is_rate_limit = True

    port = args.port
    if port is None:
        port = 4000

    web_server = WebServer(is_rate_limit, patternManager)
    web_server.run(port)


    ## main loop
    while True:

        # 1 handle web request queue
        req = web_server.get_next_request()
        while req != None:
            match req:
                case StopPattern():
                    patternManager.unload_pattern()

                case StartPattern(name=name):
                    patternManager.load_pattern(name)

                case DrawFrame(frame=frame):
                    patternManager.unload_pattern()
                    for i, pixel in enumerate(frame):
                        if (pixel != None):
                            tree.pixels[i].set_rgb(pixel[0], pixel[1], pixel[2])

                case _: 
                    pass
            req = web_server.get_next_request()

        # 2. call draw()
        patternManager.draw_current()

        # 3. get pixels from tree instance
        frame = tree.request_frame()

        # 4. send to pixel driver | blocks until space
        renderer.add_to_queue(frame)
