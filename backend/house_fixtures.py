from typing import Callable

from fixture import Graph
from network_driver import NetworkPixelDriver
from pixel_driver import driver_registry

fence_graph = Graph.from_txt("../point-clouds/house-fence.txt")
front_graph = Graph.from_txt("../point-clouds/house-front.txt")


def attach_house(fence_draw: Callable[[], None], front_draw: Callable[[], None]):
    """Run a draw function on each house fixture, sharing one device."""
    fixtures = [
        (fence_graph, fence_draw, 0),
        (front_graph, front_draw, 500),
    ]
    driver = NetworkPixelDriver("gridmastree.local", 1000, "house", fps=45, port=8420)
    for graph, draw, off in fixtures:
        driver.add_fixture(graph, off)
        graph.set_draw_fn(draw)
    driver_registry.register(driver)
