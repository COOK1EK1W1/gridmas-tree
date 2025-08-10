from typing import Optional
from colors import Pixel, tcolors
import multiprocessing

class Renderer:
    def __init__(self, coords: list[tuple[float, float, float]]):

        # create a 10 frame buffer to the pixel driver
        self.frame_queue: multiprocessing.Queue[Optional[tuple[int, list[int]]]] = multiprocessing.Queue(10)

        # select the correct pixel driver for the system, either physical or sim
        driver = self._pick_driver(len(coords))
        self.pixel_driver = driver(self.frame_queue, coords)

        self.fps = 45

        process = multiprocessing.Process(target=self.pixel_driver.run, args=())
        process.start()

    def add_to_queue(self, frame: list[int]):
        """Add a frame to the queue to be rendered
        This function blocks until there is space in the queue"""
        self.frame_queue.put((self.fps, frame))
        pass

    def _pick_driver(self, num_leds: int):
        """Pick the driver for renderign, if we have pygame use that, else we can use pixel"""
        try:
            if num_leds > 500:
                from pixel_driver import ws2812_tree_dual

                return ws2812_tree_dual.ws2812_tree_dual
            else:
                from pixel_driver import ws2812_tree

                return ws2812_tree.ws2812_tree

        except ImportError:
            print(f"{tcolors.WARNING}Using pygame simulator, Neopixels not found{tcolors.ENDC}\n")

            from pixel_driver import sim_tree
            return sim_tree.SimTree
