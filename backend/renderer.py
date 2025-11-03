"""
    Contains the renderer class that handles frames on the tree
"""

from typing import Optional
import multiprocessing
from util import tcolors

class Renderer:
    """ _summary_

    _extended_summary_
    
    Warning:
        This module is intended for internal use only. You do not need to use any of this in your pattern code
    """
    
    def __init__(self, coords: list[tuple[float, float, float]]):
        """__init__ Initialise the renderer

        Creates a new instance of Renderer, and selects the correct driver for the tree

        Args:
            coords (list[tuple[float, float, float]]): The list of LED positions on the tree
        """

        # create a 10 frame buffer to the pixel driver
        self.frame_queue: multiprocessing.Queue[Optional[tuple[int, list[int]]]] = multiprocessing.Queue(10)

        # select the correct pixel driver for the system, either physical or sim
        driver = self._pick_driver(len(coords))
        self.pixel_driver = driver(self.frame_queue, coords)

        self.fps = 45

        process = multiprocessing.Process(target=self.pixel_driver.run, args=())
        process.start()

    def add_to_queue(self, frame: list[int], fps: int):
        """Add a frame to the queue to be rendered
        This function blocks until there is space in the queue"""
        self.frame_queue.put((fps, frame))
        pass

    def _pick_driver(self, num_leds: int):
        """_pick_driver Pick the driver for rendering

        If we have pygame use that, else we can use pixel

        Args:
            num_leds (int): The number of LEDs to render

        Returns:
            Tree (ws2812_tree.ws2812_tree): Physical tree. Used if there are less than 500 LEDs
            Tree (ws2812_tree_dual.ws2812_tree_dual): Physical tree. Used if there are more than 500 LEDs
            Tree (sim_tree.SimTree): Simulated tree
        """

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
