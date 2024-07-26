import time
from multiprocessing import Queue

from rpi_ws281x import PixelStrip, Color
from pixel_driver.pixel_driver import PixelDriver


class ws2812_tree(PixelDriver):
    def __init__(self, queue: "Queue[tuple[int, list[tuple[int, int, int]]] | None]", coords: list[tuple[float, float, float]]):
        super().__init__(queue, coords)

        LED_COUNT = len(self.coords)
        # LED_COUNT = 1000
        LED_PIN = 18
        LED_FREQ_HZ = 800_000
        LED_DMA = 10
        LED_BRIGHTNESS = 255
        LED_INVERT = False
        LED_CHANNEL = 0

        strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        strip.begin()
        self.strip = strip

    def run(self):
        a = 0
        while True:
            data = self.queue.get()
            if data is None:
                break

            fps, framea = data
            for i, rgb in enumerate(framea):
                self.strip[i] = Color(rgb[1], rgb[0], rgb[2])

            time.sleep(max((1 / fps) - (time.perf_counter() - a), 0))
            a = time.perf_counter()

            self.strip.show()
