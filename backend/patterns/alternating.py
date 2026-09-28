from network_driver import NetworkPixelDriver
from pixel_driver import driver_registry
from fixture import Volume, setActiveFixture


tree = Volume.from_csv("tree.csv")
pygame = NetworkPixelDriver("127.0.0.1", tree._num_pixels, "pygame", fps=45)
pygame.add_fixture(tree, 0)
driver_registry.register(pygame)

setActiveFixture(tree)
from patterns.on import draw as on_draw
from patterns.Caduceus import draw as fireworks_draw
setActiveFixture(None)


it=120
i = 0
def display_update():
    global i
    i += 1
    if i % it > it/2:
        tree.set_draw_fn(on_draw)
    else:
        tree.set_draw_fn(fireworks_draw)

