#ifndef HW_WS2812_OUTPUT_H
#define HW_WS2812_OUTPUT_H

#include <stdint.h>

/* Drives up to PICO_NUM_LED_PINS WS2812 data lines via PIO + DMA. Frame data
 * arrives as plain RGB byte triples (see docs/docs/network-pixel-protocol.md
 * - "Plain RGB, not GRB"); this module repacks to GRB and splits across pins
 * at PICO_MAX_PIXELS_PER_PIN, mirroring the real device's channel split
 * (device/ws2812/strip.py) - except here every board has both channels ready
 * from boot regardless of how many it's actually driving (see
 * docs/docs/pico-device.md, "same firmware everywhere").
 *
 * NOT thread/core safe - call only from core1 (see main.c).
 */

void ws2812_output_init(void);

/* Pushes payload_len/3 pixels out over one or two pins, splitting at
 * PICO_MAX_PIXELS_PER_PIN. Returns once each DMA transfer is queued - each
 * call briefly blocks only long enough to confirm the *previous* transfer on
 * a given pin has finished (there's no double-buffering here yet; at 45fps
 * and <=500px/pin this practically never stalls, since a full transfer takes
 * ~15ms against a ~22ms frame interval - see docs/docs/pico-device.md for
 * this known simplification). */
void ws2812_output_show(const uint8_t *rgb, uint16_t payload_len);

/* All pins to all-zero. */
void ws2812_output_blank(void);

#endif
