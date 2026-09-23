"""Flask side of the GRIDmas Tree network pixel protocol's control plane -
see docs/docs/network-pixel-protocol.md for the wire spec and
backend/network_driver.py for the client.

Frame data (and the device's readiness signal) is WebSocket, not HTTP -
see ws_server.py. This module only ever serves GET /status and POST /clear.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from flask import Flask, jsonify

if TYPE_CHECKING:
    from scheduler import FrameScheduler, Strip

FIRMWARE_VERSION = "1.0.0"


def create_app(strip: Strip, scheduler: FrameScheduler, device_name: str, target_fps: int) -> Flask:
    app = Flask(__name__)
    started = time.time()

    @app.get("/status")
    def status():
        now = time.time()
        return jsonify({
            "device_name": device_name,
            "pixel_count": strip.pixel_count,
            "target_fps": target_fps,
            "firmware_version": FIRMWARE_VERSION,
            "uptime_s": now - started,
            "clock": now,
            "queue": {"depth": scheduler.depth(), "capacity": scheduler.capacity},
            "stats": scheduler.snapshot_stats(),
        })

    @app.post("/clear")
    def clear():
        scheduler.clear()
        return "", 200

    return app
