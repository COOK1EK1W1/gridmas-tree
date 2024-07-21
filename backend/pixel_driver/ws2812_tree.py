import time
from multiprocessing import Queue

from rpi_ws281x import PixelStrip
import _rpi_ws281x as ws
from pixel_driver.pixel_driver import PixelDriver


class ws2812_tree(PixelDriver):
    def __init__(self, queue: "Queue[list[tuple[int, int, int]] | None]", coords: list[tuple[float, float, float]]):
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
            if self.queue.qsize() > 3:
                framea = self.queue.get(False)
                if framea is None:
                    break

                for i, (r, g, b) in enumerate(framea):
                    ws.ws2811_led_set(strip._channel, i, (r << 16) | (g << 8) | b)
                    # self.strip[i] = Color(rgb[1], rgb[0], rgb[2])

                time.sleep(max((1 / 45) - (time.perf_counter() - a), 0))
                a = time.perf_counter()

                self.strip.show()
