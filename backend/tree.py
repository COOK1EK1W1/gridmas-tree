from typing import Callable
from pixel_driver.pixel_driver import PixelDriver
from util import STOPFLAG, generate_distance_map, linear, read_tree_csv
import multiprocessing
import time
import sys
from colors import tcolors, Color, Pixel


def pick_driver(num_leds: int) -> type[PixelDriver]:
    try:
        if num_leds > 500:
            from pixel_driver import ws2812_tree_dual

            return ws2812_tree.ws2812_tree_dual
        else:
            from pixel_driver import ws2812_tree

            return ws2812_tree.ws2812_tree

    except ImportError:
        print(f"{tcolors.WARNING}Cannot find neopixel module, probably because you're running on a device which is not supported")
        print(f"will attempt to run in dev mode{tcolors.ENDC}\n")

        from pixel_driver import sim_tree
        return sim_tree.SimTree


class Tree():
    """This is the main way to modify the pixels on the tree. 
    
    
       To use in your file, import as follows:
         from tree import tree
       
       After this, you can modify the pixels on the tree as such:
         def main():
           for pixel in tree.pixels:
             pixel.set_rgb(0, 0, 0)
           
       Attributes:
         pixels: list[Pixel]: Pixel buffer held by the tree. Gets pushed to pixel driver on every update. The arry is in the same order as the lights on the strip
         coords: list[tuple[float, float, float]]: A list of 3d coordinates (x,y,z) which is in ordeer of pixels on the strip i.e. parrallel with tree.pixels
         num_pixels: int: The number of pixels on the tree. Same as doing len(tree.pixels)
         height: float: Height of the tree
         distances: list[list[float]]: A 2d array which holds pre-computed 3D euclidean distances between all pairs of pixels. The index of each array is parrallel with tree.pixels
    """
    def __init__(self):
        self.fps = 45

        self.coords = read_tree_csv()

        self.num_pixels = int(len(self.coords))

        # create a 10 frame buffer to the pixel driver
        self.frame_queue: multiprocessing.Queue[tuple[int, list[int]] | None] = multiprocessing.Queue(10)

        # select the correct pixel driver for the system, either physical or sim
        driver = pick_driver(self.num_pixels)
        self.pixel_driver = driver(self.frame_queue, self.coords)

        self.height = max([x[2] for x in self.coords])

        self.distances = generate_distance_map(self.coords)

        total_size = sys.getsizeof(self.distances)
        for row in self.distances:
            for element in row:
                total_size += sys.getsizeof(element)
        print("Size of the distance array in bytes:", total_size)

        self.pixels: list[Pixel] = [Pixel((x[0], x[1], x[2])) for x in self.coords]

        self.last_update = time.perf_counter()
        self.render_times: list[float] = []

        self.stop_flag = False

    def set_light(self, n: int, color: Color):
        """Set the Nth light in the strip to the specified color

        Args:
            n (int): The light you want to set
            color (Color): The color that you want to set the light to
        """
        self.pixels[n].set_color(color)

    def get_light(self, n: int) -> Pixel:
        """Get the Nth light on the strip

        Args:
            n (int): The light you want to retrieve

        Returns:
            Pixel: The light that you have requested. You can then set the color of it directly
        """
        return self.pixels[n]

    def update(self):
        """This pushes the pixel buffer to the pixel driver, for pc use this pushes
           the buffer to the pygame+openGL simulator , when ran on a raspberry pi it
           will push it to the LED strip

           Update also regulates the frame rate; typically the tree will 
           target 45 fps, if your pattern runs faster than 22ms it will sleep the
           rest of the time until its time to generate a new frame. This shouldn't 
           affect the end developer, as they should just think of the main while 
           loop running every 22ms

        Raises:
            STOPFLAG
        """
        t = time.perf_counter()
        render_time = t - self.last_update
        self.render_times.append(render_time)

        # add frame to frame queue, if frame queue is full, then this blocks until space
        self.frame_queue.put((self.fps, list(map(lambda x: x.to_int(), self.pixels))))

        if self.stop_flag:
            raise STOPFLAG("cancel")

        if len(self.render_times) > 100:
            self.render_times.pop(0)

        if len(self.render_times) != 0:
            avgrender = sum(self.render_times) / len(self.render_times)

            if avgrender != 0:
                print(f"render: {str(avgrender*1000)[0:5]}ms ps: {round((avgrender / (1/tree.fps))*100, 2)}%       ", end="\r")
        self.last_update = time.perf_counter()

    def set_fps(self, fps: int):
        """Allows you to change the speed that you want the animation to run at.
           If unset, the default fps is 45

        Args:
            fps (int): target fps for the animation. 
        """
        self.fps = fps

    def run(self):
        """Internal
        """
        process = multiprocessing.Process(target=self.pixel_driver.run, args=())
        print("running the processs")
        process.start()

    def fade(self, n: float = 1.1):
        """Fade the entire tree. 
           n<1 will cause the tree to become brighter.
           tree.lerp(0, 0, 0) is prefered to tree.fade() as it if more performant
           and gived better cotnrol over timing.

        Args:
            n (float, optional): Unknown. Defaults to 1.1.
        """
        for pixel in self.pixels:
            pixel.fade(n)

    def black(self):
        """Sets all pixels on the tree to black (0, 0, 0)
        """
        for pixel in self.pixels:
            pixel.set_rgb(0, 0, 0)

    def fill(self, color: Color):
        """Set all lights on the tree to one color

        Args:
            color (Color): The color you want to set the tree to
        """
        for pixel in self.pixels:
            pixel.set_color(color)

    def lerp(self, color: Color, frames: int, fn: Callable[[float], float] = linear):
        """Lerp the entire tree from its current color to the target color over the specified amount of frames

        Args:
            color (Color): Target color
            frames (int): The number of frames to perform the lerp over
            fn (Callable[[float], float], optional): Unsure. Defaults to linear.
        """
        for pixel in self.pixels:
            pixel.lerp(color.to_tuple(), frames, fn=fn)

    def sleep(self, frames: int, allow_lerp: bool = False):
        """_summary_

        Args:
            frames (int): _description_
            allow_lerp (bool, optional): _description_. Defaults to False.
        """
        for _ in range(frames):
            if allow_lerp:
                for pixel in tree.pixels:
                    pixel.cont_lerp()
            self.update()


tree = Tree()
