"""Shared WSGI entry point for the device servers (main.py, simulate.py)."""


def serve(app, host: str, port: int):
    """Serve under waitress (proper keep-alive and a thread pool, still Pi-light);
    fall back to Flask's dev server, which handles sustained streaming poorly."""
    try:
        from waitress import serve as waitress_serve
    except ImportError:
        print("waitress not installed - using the slower Flask dev server (`pip install waitress`)")
        app.run(host=host, port=port, threaded=True)
    else:
        waitress_serve(app, host=host, port=port, threads=8, channel_timeout=30)
