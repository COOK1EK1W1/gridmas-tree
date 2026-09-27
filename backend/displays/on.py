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


it=60
i = 0
def update():
    global i
    i += 1
    print(i)
    if i % it > it/2:
        tree.draw_fn = on_draw
    else:
        tree.draw_fn = fireworks_draw

