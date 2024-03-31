from util import tree
import time

def doStrip():
    while True:
        for i in range(tree.num_pixels):
            tree.set_light(i, (255, 255, 255))
            for ia in range(tree.num_pixels):
                r, g, b = tree.get_light(ia)
                tree.set_light(ia, (int(r/1.1), int(g/1.1), int(b/1.1)))
            tree.update()
            time.sleep(0.01)


if __name__ == "__main__":
    doStrip()
