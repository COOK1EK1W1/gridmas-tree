#!/usr/bin/python3

from pixel_driver import driver_registry
from pattern_manager import PatternManager
from web_server import StartPattern, StopPattern, WebServer, RandomPattern
import argparse
import signal
import sys
import time
import random

# add the command line arguments
parser = argparse.ArgumentParser(
    prog="GRIDmas Tree - Main",
    description="This is the main entry point for the GRIDmas Tree web server",
    epilog="GRIDmas Tree is inspired by Matt Parkers 500 LED christmas tree. Please see his videos on the subject, they are a very good watch!"
)

parser.add_argument("--port", type=int, required=False, help="The port to host the Web Server")
parser.add_argument("--rate-limit", action="store_true", required=False, help="Use this to enable rate limiting on the web server")
parser.add_argument("--pattern-dir", type=str, required=False, help="Specify the directory where pattern files are stored")
parser.add_argument("--auto-pattern", type=int, required=False, help="Automatically run through random patterns at the interval you set")

def signal_handler(sig, frame):
    print("\nShutting down gracefully...")
    if web_server:
        web_server.stop()
    sys.exit(0)

if __name__ == '__main__':
    args = parser.parse_args()

    # Set up signal handling for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start pattern manager and load patterns
    patternManager = PatternManager(args.pattern_dir or "patterns/", driver_registry)
    

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
    time.sleep(0.2)
    print(f"Web server started on port {port}")

    t = 0
    last_change = time.time()

    ## main loop
    try:
        while True:
            t += 1

            if (auto_pattern is not None and time.time() - last_change > auto_pattern):
                web_server.request_queue.put(RandomPattern())

            # 1 handle web request queue
            req = web_server.get_next_request()
            handled_request = req is not None
            while req != None:
                match req:
                    case StopPattern():
                        patternManager.unload_pattern()

                    case StartPattern(name=name):
                        patternManager.load_pattern(name)
                        last_change = time.time() + 300 
                        # Make user selected patterns run for 5 mins from the point they start

                    case RandomPattern():
                        patternManager.unload_pattern()
                        a = list(patternManager.list_patterns())
                        random.shuffle(a)
                        patternManager.load_pattern(a[0])
                        last_change = time.time()

                    case _: 
                        pass
                req = web_server.get_next_request()

            patternManager.run_display_update()

            # 4. send to pixel driver
            produced_frame = driver_registry.draw_and_flush_drivers()

            # yield instead of busyloop just incase
            if not handled_request and not produced_frame:
                time.sleep(0.0001)

    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        web_server.stop()
    except Exception as e:
        print(f"Error in main loop: {e}")
        web_server.stop()
        raise
