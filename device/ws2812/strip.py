"""Thin wrapper around the low-level `_rpi_ws281x` bindings for one or two
WS2812 channels (GPIO18 and GPIO13 are the PWM-capable pins the DMA driver can
drive).

`ws2811_render()` only queues the frame for the Pi's DMA+PWM hardware and
returns straight away - it doesn't block for the ~30us/pixel the hardware takes
to shift the bits out. That is what lets FrameScheduler keep receiving and
timing the next frames while the current one is still being written.
"""

from typing import List, Tuple

import numpy as np
import _rpi_ws281x as ws


class Ws2812Strip:
    """Drives one or two WS2812 channels over DMA."""

    LED_FREQ_HZ = 800_000
    LED_INVERT = 0
    LED_BRIGHTNESS = 255

    def __init__(self, channels: List[Tuple[int, int]], dma_channel: int = 10):
        if not 1 <= len(channels) <= 2:
            raise ValueError(f"Ws2812Strip supports 1 or 2 channels, got {len(channels)}")

        self._channels = channels
        self.pixel_count = sum(count for _, count in channels)

        self._leds = ws.new_ws2811_t()
        ws.ws2811_t_freq_set(self._leds, self.LED_FREQ_HZ)
        ws.ws2811_t_dmanum_set(self._leds, dma_channel)

        # any unused second channel stays as new_ws2811_t() zero-initialised it
        for ch, (pin, count) in enumerate(channels):
            channel = ws.ws2811_channel_get(self._leds, ch)
            ws.ws2811_channel_t_gpionum_set(channel, pin)
            ws.ws2811_channel_t_count_set(channel, count)
            ws.ws2811_channel_t_invert_set(channel, self.LED_INVERT)
            ws.ws2811_channel_t_brightness_set(channel, self.LED_BRIGHTNESS)
            ws.ws2811_channel_t_strip_type_set(channel, ws.WS2811_STRIP_GRB)

        self._check(ws.ws2811_init(self._leds), "ws2811_init")

        # cache (handle, start, count) per channel so render() does no per-frame setup
        self._targets: List[Tuple[object, int, int]] = []
        start = 0
        for ch, (_, count) in enumerate(channels):
            self._targets.append((ws.ws2811_channel_get(self._leds, ch), start, count))
            start += count

    @staticmethod
    def _check(resp: int, call: str):
        if resp != ws.WS2811_SUCCESS:
            raise RuntimeError(f"{call} failed with code {resp} ({ws.ws2811_get_return_t_str(resp)})")

    def render(self, rgb: bytes):
        """Push a full frame - pixel_count RGB byte-triples, channel 0's pixels first - out over DMA."""
        if len(rgb) != self.pixel_count * 3:
            raise ValueError(f"expected {self.pixel_count * 3} bytes, got {len(rgb)}")

        # pack to the driver's GRB int format in one vectorised pass, so the only
        # per-pixel work left is the FFI call and the GIL is released quickly
        c = np.frombuffer(rgb, dtype=np.uint8).astype(np.uint32)
        packed = ((c[0::3] << 8) | (c[1::3] << 16) | c[2::3]).tolist()

        for channel, start, count in self._targets:
            for i, value in enumerate(packed[start:start + count]):
                ws.ws2811_led_set(channel, i, value)

        self._check(ws.ws2811_render(self._leds), "ws2811_render")

    def clear(self):
        self.render(bytes(self.pixel_count * 3))

    def close(self):
        self.clear()
        ws.ws2811_fini(self._leds)
