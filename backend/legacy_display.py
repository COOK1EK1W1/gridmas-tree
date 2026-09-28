"""The display that draw()-only patterns are wrapped in, so they run on the tree without a display file of their own."""

from typing import Callable, Generator, Optional
from fixture import Volume
from pixel_driver import PixelDriver, driver_registry


tree = Volume.from_csv("tree.csv")


def _make_driver() -> PixelDriver:
    try:
        from network_driver import NetworkPixelDriver
    except ImportError:
        # the web editor's pyodide runtime has no requests, the browser pulls frames instead
        from web_driver import WebPixelDriver
        return WebPixelDriver(tree._num_pixels, "tree", fps=45)
    return NetworkPixelDriver("127.0.0.1", tree._num_pixels, "tree", fps=45)


def attach(draw_fn: Callable[[], Optional[Generator[None, None, None]]]):
    driver = _make_driver()
    driver.add_fixture(tree, 0)
    driver_registry.register(driver)
    tree.set_draw_fn(draw_fn)
