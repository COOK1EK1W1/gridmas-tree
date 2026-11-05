from fixture import Graph
from network_driver import NetworkPixelDriver
from pixel_driver import driver_registry

fence_graph = Graph.from_txt("../point-clouds/house-fence.txt")
front_graph = Graph.from_txt("../point-clouds/house-front.txt")
hedge_wall = Graph.from_txt("../point-clouds/house-hedge.txt")


def attach(fps: float = 45):
    """Connect the house for a pattern. Unloading a pattern closes its drivers, and this
    module is only imported once, so every load makes new ones"""
    pi01 = NetworkPixelDriver("gridmastree.local", 1000, "pi01", port=8420)
    pi02 = NetworkPixelDriver("gridmas-pi02.local", 1000, "pi02", port=8420)

    pi01.add_fixture(fence_graph, 0)
    pi01.add_fixture(front_graph, 500)
    pi02.add_fixture(hedge_wall, 0)

    # the fixtures outlive the pattern that last drew on them
    for fixture in (fence_graph, front_graph, hedge_wall):
        fixture.set_draw_fn(None)

    for driver in (pi01, pi02):
        driver.fps = fps
        driver_registry.register(driver)
