from pixel import Pixel
from multiprocessing import Queue

from rpi_ws281x import PixelStrip
from pixel_driver.pixel_driver import PixelDriver


class ws2812_tree(PixelDriver):
    def __init__(self, queue: "Queue[list[Pixel] | None]", coords: list[tuple[float, float, float]]):
        self.queue = queue
        self.coords = coords

        LED_COUNT = 500
        LED_PIN = 18
        LED_FREQ_HZ = 800_000
        LED_DMA = 10
        LED_BRIGHTNESS = 255
        LED_INVERT = False
        LED_CHANNEL = 0

        strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        strip.begin()

    def run(self):
        while True:
            if not self.queue.empty():
                args = self.queue.get()
                if args is None:
                    break
                for i, pixel in enumerate(args):
                    self.pixels[i] = pixel.toTuple()
                self.buffer = [x for x in self.pixels]
