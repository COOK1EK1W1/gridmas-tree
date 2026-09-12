#!/usr/bin/env python3
"""Standalone WS2812 device server for the GRIDmas Tree network pixel protocol.

Runs on the Raspberry Pi wired to the LED strip(s), not on the pattern-computing
controller. It hosts the protocol from docs/docs/network-pixel-protocol.md -
a UDP frame receiver (../common/udp_frame.py) plus an HTTP server for
/status and /clear (../common/app.py) - buffers incoming frames, and plays
each one back at its tagged wall-clock time. Rendering (strip.py) runs on
its own thread (../common/scheduler.py) so it never blocks, or is blocked
by, frame reception. See backend/network_driver.py for the client, and
../pygame/ for a hardware-free stand-in device.

Needs root for the PWM+DMA hardware:
    sudo python3 main.py --channel 18:500 --name pi1
    sudo python3 main.py --channel 18:500 --channel 13:500 --port 8420
"""

import argparse
import os
import signal
import sys

# protocol code shared by every device type - see device/common/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))


def parse_channel(value: str) -> "tuple[int, int]":
    try:
        pin, count = value.split(":")
        return int(pin), int(count)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected PIN:COUNT (e.g. 18:500), got {value!r}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gridmas-device",
        description="WS2812 device server - receives timestamped frames over UDP and drives 1-2 LED strips via DMA.",
    )
    p.add_argument("--channel", type=parse_channel, action="append", required=True, metavar="PIN:COUNT",
                   help="GPIO pin and pixel count for one output channel, e.g. 18:500. Pass once or twice.")
    p.add_argument("--port", type=int, default=8420, help="Port to listen on (default: 8420)")
    p.add_argument("--name", default="gridmas-device", help="Device name reported in /status")
    p.add_argument("--dma", type=int, default=10, help="DMA channel for signal generation (default: 10)")
    p.add_argument("--fps", type=int, default=45,
                   help="Expected frame rate; sizes the buffer and is reported in /status (default: 45)")
    p.add_argument("--buffer-seconds", type=float, default=2.0,
                   help="Seconds of frames to buffer ahead; match the controller's PREROLL+BUFFER (default: 2.0)")
    p.add_argument("--late-grace", type=float, default=0.2,
                   help="Drop frames later than this many seconds past their presentation time (default: 0.2)")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    if len(args.channel) > 2:
        parser.error("at most 2 --channel arguments are supported")

    # imported here, after arg parsing, so --help works without the hardware libs
    from app import create_app
    from scheduler import FrameScheduler
    from strip import Ws2812Strip
    from udp_frame import UdpFrameServer
    from wsgi import serve

    strip = Ws2812Strip(args.channel, dma_channel=args.dma)
    scheduler = FrameScheduler(
        strip,
        capacity=max(1, int(args.fps * args.buffer_seconds)),
        late_grace_s=args.late_grace,
    )
    udp_server = UdpFrameServer(scheduler, args.port)
    udp_server.start()

    def shutdown(*_):
        print("\nshutting down...")
        udp_server.stop()
        scheduler.stop()
        strip.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    channels = ", ".join(f"gpio{pin}x{count}" for pin, count in args.channel)
    print(f"{args.name}: {strip.pixel_count} pixels ({channels}), "
          f"frames on udp:{args.port}, status/clear on http:{args.port}")
    serve(create_app(strip, scheduler, args.name, args.fps), host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
