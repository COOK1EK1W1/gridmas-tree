#!/usr/bin/env python3
"""Pygame-window stand-in for a physical WS2812 device.

Speaks the exact same network pixel protocol as ../ws2812/main.py's real
device server (../common/app.py, ../common/scheduler.py, ../common/udp_frame.py)
- only the strip differs: sim_strip.py draws to a window instead of driving
GPIO/DMA. A NetworkPixelDriver on the controller can't tell the two apart.
No root and no Pi hardware needed - run as many instances as you like, each
on its own --port, to simulate several devices/fixtures at once:

    python3 simulate.py --tree-file ../../tree.csv --port 8420 --name sim1
    python3 simulate.py --tree-file ../../tree.csv --port 8421 --name sim2

Requires pygame/PyOpenGL: `pip install -r device/pygame/requirements.txt`.
"""

import argparse
import csv
import os
import sys
import threading

# protocol code shared by every device type - see device/common/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))

from app import create_app
from scheduler import FrameScheduler
from sim_strip import SimStrip
from udp_frame import UdpFrameServer
from wsgi import serve


def read_tree_csv(path: str) -> list[tuple[float, float, float]]:
    with open(path, newline="") as f:
        return [(float(x), float(y), float(z)) for x, y, z in csv.reader(f)]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gridmas-simulate",
        description="Pygame-window device server - stands in for a physical WS2812 device over the network pixel protocol.",
    )
    p.add_argument("--tree-file", default="tree.csv", help="Path to the LED coordinate map (default: tree.csv)")
    p.add_argument("--port", type=int, default=8420, help="Port to listen on (default: 8420)")
    p.add_argument("--name", default="gridmas-sim", help="Device name reported in /status and the window title")
    p.add_argument("--fps", type=int, default=45,
                   help="Expected frame rate; sizes the buffer and is reported in /status (default: 45)")
    p.add_argument("--buffer-seconds", type=float, default=2.0,
                   help="Seconds of frames to buffer ahead; match the controller's PREROLL+BUFFER (default: 2.0)")
    p.add_argument("--late-grace", type=float, default=0.2,
                   help="Drop frames later than this many seconds past their presentation time (default: 0.2)")
    p.add_argument("--window-size", type=int, nargs=2, default=(800, 600), metavar=("W", "H"))
    return p


def main():
    args = build_parser().parse_args()

    strip = SimStrip(read_tree_csv(args.tree_file), name=args.name, window_size=tuple(args.window_size))
    scheduler = FrameScheduler(
        strip,
        capacity=max(1, int(args.fps * args.buffer_seconds)),
        late_grace_s=args.late_grace,
    )

    udp_server = UdpFrameServer(scheduler, args.port)
    udp_server.start()

    app = create_app(strip, scheduler, args.name, args.fps)
    threading.Thread(target=serve, args=(app, "0.0.0.0", args.port), daemon=True).start()
    print(f"{args.name}: {strip.pixel_count} pixels, "
          f"frames on udp:{args.port}, status/clear on http:{args.port}")

    # pygame/OpenGL need the window on the main thread; the HTTP/UDP servers run above it
    try:
        strip.run()
    except KeyboardInterrupt:
        pass
    finally:
        udp_server.stop()
        scheduler.stop()


if __name__ == "__main__":
    main()
