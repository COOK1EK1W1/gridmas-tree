"""This is the main entry point for GRIDmas Tree."""

__author__ = "Cairan Cook"
"""Code Author"""

__documenter__ = "Owen Plimer"
"""Documentation author"""

#!/usr/bin/python3

from renderer import Renderer
from pattern_manager import PatternManager
from tree import tree
from web_server import DrawFrame, StartPattern, StopPattern, WebServer, RandomPattern
import argparse
import signal
import sys
import time
import random

import cProfile
import pstats

# add the command line arguments
parser = argparse.ArgumentParser(
    prog="GRIDmas Tree - Main",
    description="This is the main entry point for the GRIDmas Tree web server",
    epilog="GRIDmas Tree is inspired by Matt Parkers 500 LED christmas tree. Please see his videos on the subject, they are a very good watch!"
)

parser.add_argument("--port", type=int, required=False, help="The port to host the Web Server")
parser.add_argument("--tree-file", type=str, required=False, help="Specify where to find the tree.csv file")
parser.add_argument("--rate-limit", action="store_true", required=False, help="Use this to enable rate limiting on the web server")
parser.add_argument("--pattern-dir", type=str, required=False, help="Specify the directory where pattern files are stored")
parser.add_argument("--auto-pattern", type=int, required=False, help="Automatically run through random patterns at the interval you set")

def signal_handler(sig, frame):
    print("\nShutting down gracefully...")
    if web_server:
        web_server.stop()
    sys.exit(0)


def main():
    args = parser.parse_args()

    # Set up signal handling for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # initialise tree
    tree.init(args.tree_file or "backend/tree.csv")

    # Start pattern manager and load patterns
    patternManager = PatternManager(args.pattern_dir or "backend/patterns/")

    tree._fps = 99999

    # Initialise the rendering pipeline
    renderer = Renderer(tree._coords)

    # Web server
    is_rate_limit = False
    if args.rate_limit:
        is_rate_limit = True

    port = args.port
    if port is None:
        port = 4000

    auto_pattern = args.auto_pattern

    web_server = WebServer(is_rate_limit, patternManager)
    web_server.run(port)

    # Give the web server a moment to start up
    time.sleep(0.5)
    print(f"Web server started on port {port}")

    t = 0
    last_change = time.time()

    print(auto_pattern)
    ## main loop
    try:
        while True:
            t += 1

            if (auto_pattern is not None and time.time() - last_change > auto_pattern):
                web_server.request_queue.put(RandomPattern())

            # 1 handle web request queue
            req = web_server.get_next_request()
            while req != None:
                match req:
                    case StopPattern():
                        patternManager.unload_pattern()

                    case StartPattern(name=name):
                        tree._pattern_reset()
                        patternManager.load_pattern(name)

                    case DrawFrame(frame=frame):
                        patternManager.unload_pattern()
                        for i, pixel in enumerate(frame):
                            if (pixel != None):
                                tree._pixels[i].set_rgb(pixel[0], pixel[1], pixel[2])

                    case RandomPattern():
                        tree._pattern_reset()
                        patternManager.unload_pattern()
                        a = list(patternManager.patterns.keys())
                        random.shuffle(a)
                        patternManager.load_pattern(a[0])
                        last_change = time.time()

                    case _: 
                        pass
                req = web_server.get_next_request()

            # 2. call draw()
            patternManager.draw_current()

            # 3. get pixels from tree instance
            frame = tree._request_frame()
            fps = tree._fps

            # 4. send to pixel driver | blocks until space
            renderer.add_to_queue(frame, fps)

    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        web_server.stop()
    except Exception as e:
        print(f"Error in main loop: {e}")
        web_server.stop()
        raise

if __name__ == '__main__':
    profiler = cProfile.Profile()
    try:
        profiler.enable()
        main()
    finally:
        profiler.disable()
        profiler.dump_stats("gridmas.prof")