from network_driver import NetworkPixelDriver
from pixel_driver import driver_registry
from fixture import Volume, setActiveFixture


tree = Volume.from_csv("tree.csv")
pygame = NetworkPixelDriver("127.0.0.1", tree._num_pixels, "pygame", fps=45)
pygame.add_fixture(tree, 0)
driver_registry.register(pygame)

setActiveFixture(tree)
from patterns.on import draw as on_draw
tree.draw_fn = on_draw
setActiveFixture(None)
def update():
    pass

