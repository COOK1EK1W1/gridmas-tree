from multiprocessing import Queue

import _rpi_ws281x as ws
from rpi_ws281x import PixelStrip
from pixel_driver.pixel_driver import PixelDriver


class ws2812_tree(PixelDriver):
    def __init__(self, queue: "Queue[tuple[int, list[int]] | None]", coords: list[tuple[float, float, float]]):
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

    def draw(self, frame: list[int]):
        for i, rgb in enumerate(frame):
            ws.ws2811_led_set(self.strip._channel, i, rgb)

    def show(self):
        self.strip.show()
