#ifndef CORE_FRAME_BUFFER_H
#define CORE_FRAME_BUFFER_H

#include <stdbool.h>
#include <stdint.h>

#include "pico_config.h"

/* Fixed-size, statically-allocated presentation-time buffer.
 *
 * Mirrors device/common/scheduler.py's behaviour (buffer up to N whole
 * frames, always show the earliest-due one, drop anything shown too late)
 * without a heap or dynamic allocation - every frame_buffer_t is one
 * fixed-size struct, sized at compile time by PICO_FRAME_SLOT_COUNT /
 * PICO_MAX_PIXELS_TOTAL. See docs/docs/network-pixel-protocol.md for the
 * wire format and flow-control scheme this implements.
 *
 * NOT thread/core safe on its own - this module has no Pico SDK dependency
 * so it can be built and unit-tested on a host machine (see test/). Callers
 * on the device (hw/ws_frame_server.c on core0, main.c's core1 loop) are
 * responsible for serialising concurrent access, e.g. with a
 * pico/critical_section.h critical section around each call.
 */

typedef struct {
    int64_t  presentation_time_us; /* unix epoch, microseconds */
    uint32_t seq;
    uint16_t payload_len;          /* bytes actually used; pixel_count * 3 */
    uint8_t  payload[PICO_MAX_PIXELS_TOTAL * 3];
} frame_t;

typedef struct {
    frame_t slots[PICO_FRAME_SLOT_COUNT];
    bool    occupied[PICO_FRAME_SLOT_COUNT];

    uint32_t frames_received;
    uint32_t frames_shown;
    uint32_t frames_dropped_late;
    uint32_t frames_dropped_queue_full;
    uint32_t frames_rejected_bad_payload; /* payload_len 0 or too big - see frame_buffer_submit_frame */
} frame_buffer_t;

void frame_buffer_init(frame_buffer_t *fb);

/* Submit one whole frame - a WS message arrives complete and in order
 * (unlike the old UDP chunks), so there's no reassembly step. Evicts the
 * single earliest-due occupied slot first if the buffer is full (matches
 * network_driver.py's client-side "drop oldest" policy) rather than
 * declining, same as before - see docs/docs/pico-device.md for why this
 * device type never refuses. Rejects (returns false, changes nothing) a
 * payload_len of 0 or too big for one slot. */
bool frame_buffer_submit_frame(frame_buffer_t *fb, int64_t presentation_time_us, uint32_t seq,
                                const uint8_t *payload, uint16_t payload_len);

typedef enum {
    FRAME_BUFFER_NONE,  /* nothing to show right now */
    FRAME_BUFFER_READY, /* *out holds a frame due to be shown */
    FRAME_BUFFER_LATE,  /* a frame was dropped for being too late; stats updated, *out untouched */
} frame_buffer_poll_result_t;

/* Called once per scheduler tick (core1). Finds the earliest-due occupied
 * slot; if it's within late_grace_us of now, copies it into *out and frees
 * the slot (FRAME_BUFFER_READY); if it's later than that, frees the slot
 * without copying it and counts it dropped (FRAME_BUFFER_LATE); if the
 * earliest slot isn't due yet (or the buffer is empty), does nothing
 * (FRAME_BUFFER_NONE). Resolves at most one slot per call - call again to
 * drain a backlog. */
frame_buffer_poll_result_t frame_buffer_poll(frame_buffer_t *fb, int64_t now_us,
                                              int64_t late_grace_us, frame_t *out);

uint32_t frame_buffer_depth(const frame_buffer_t *fb);

/* PICO_FRAME_SLOT_COUNT - frame_buffer_depth(fb) - the CREDIT value
 * hw/ws_frame_server.c reports to the controller. */
uint32_t frame_buffer_free_slots(const frame_buffer_t *fb);

#endif
