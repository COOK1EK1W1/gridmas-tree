from ctypes import c_uint32, POINTER, cast
import threading
from multiprocessing import Queue

from multiprocessing import Queue
import _rpi_ws281x as ws
from ctypes import c_uint32
from pixel_driver.pixel_driver import PixelDriver
import _rpi_ws281x as ws
from pixel_driver.pixel_driver import PixelDriver


class ws2812_tree(PixelDriver):
    def __init__(self, queue: "Queue[tuple[int, list[int]] | None]", coords: list[tuple[float, float, float]]):

        super().__init__(queue, coords)

        self.LED_COUNT = [500, 500]    # Number of LEDs per strip
        self.LED_PIN = [18, 13]        # GPIO pins
        self.LED_FREQ_HZ = 800000
        self.LED_DMA = 10              # DMA channel
        self.LED_BRIGHTNESS = 255
        self.LED_INVERT = False

        # Create ws2811_t structure and initialize channels
        self.leds = ws.new_ws2811_t()

        for ch in [0, 1]:
            channel = ws.ws2811_channel_get(self.leds, ch)
            ws.ws2811_channel_t_count_set(channel, self.LED_COUNT[ch])
            ws.ws2811_channel_t_gpionum_set(channel, self.LED_PIN[ch])
            ws.ws2811_channel_t_invert_set(channel, int(self.LED_INVERT))
            ws.ws2811_channel_t_brightness_set(channel, self.LED_BRIGHTNESS)
            ws.ws2811_channel_t_strip_type_set(channel, ws.WS2811_STRIP_GRB)

        ws.ws2811_t_freq_set(self.leds, self.LED_FREQ_HZ)
        ws.ws2811_t_dmanum_set(self.leds, self.LED_DMA)

        # Initialize library with LED configuration.
        resp = ws.ws2811_init(self.leds)
        if resp != ws.WS2811_SUCCESS:
            message = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError(f'ws2811_init failed with code {resp} ({message})')

    def draw(self, frame: list[int]):
        # Convert frame list to ctypes array
        frame_array = (c_uint32 * len(frame))(*frame)

        # Update channel 0
        channel_0 = ws.ws2811_channel_get(self.leds, 0)
        for i in range(self.LED_COUNT[0]):
            ws.ws2811_led_set(channel_0, i, frame_array[i])

        # Update channel 1
        channel_1 = ws.ws2811_channel_get(self.leds, 1)
        for i in range(self.LED_COUNT[1]):
            ws.ws2811_led_set(channel_1, i, frame_array[i + self.LED_COUNT[0]])

    def show(self):
        # Render all channels at once
        resp = ws.ws2811_render(self.leds)
        if resp != ws.WS2811_SUCCESS:
            message = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError(f'ws2811_render failed with code {resp} ({message})')
