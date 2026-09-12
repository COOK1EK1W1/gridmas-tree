#ifndef CORE_FRAME_BUFFER_H
#define CORE_FRAME_BUFFER_H

#include <stdbool.h>
#include <stdint.h>

#include "pico_config.h"

/* Fixed-size, statically-allocated frame buffer + due-frame scheduler.
 *
 * Mirrors device/common/scheduler.py's behaviour (reassemble chunks, buffer
 * up to N completed frames, always show the earliest-due one, drop
 * anything shown too late, NAK a chunk that's stalled a gap) without a heap
 * or dynamic allocation - every frame_buffer_t is one fixed-size struct,
 * sized at compile time by PICO_FRAME_SLOT_COUNT / PICO_MAX_PENDING_FRAMES /
 * PICO_MAX_PIXELS_TOTAL. See docs/docs/network-pixel-protocol.md for the
 * wire format and gap-detection scheme this implements.
 *
 * NOT thread/core safe on its own - this module has no Pico SDK dependency
 * so it can be built and unit-tested on a host machine (see test/). Callers
 * on the device (hw/udp_frame_server.c on core0, main.c's core1 loop) are
 * responsible for serialising concurrent access, e.g. with a
 * pico/critical_section.h critical section around each call.
 */

typedef struct {
    int64_t  presentation_time_us; /* unix epoch, microseconds */
    uint32_t seq;
    uint16_t payload_len;          /* bytes actually used; pixel_count * 3 */
    uint8_t  payload[PICO_MAX_PIXELS_TOTAL * 3];
} frame_t;

/* A frame that hasn't had all its chunks arrive yet. */
typedef struct {
    bool     in_use;
    uint32_t seq;
    int64_t  presentation_time_us;
    uint8_t  chunk_count;
    uint32_t received_mask;    /* bit i set => chunk i has arrived */
    uint32_t naked_mask;       /* bit i set => a NAK has already been sent for chunk i */
    uint32_t stall_count;      /* later frames completed while this one is still pending */
    uint16_t total_len;        /* bytes assembled so far */
    uint8_t  payload[PICO_MAX_PIXELS_TOTAL * 3];
} pending_frame_t;

typedef struct {
    uint32_t seq;
    uint8_t  chunk_index;
} nak_t;

typedef struct {
    frame_t slots[PICO_FRAME_SLOT_COUNT];
    bool    occupied[PICO_FRAME_SLOT_COUNT];

    pending_frame_t pending[PICO_MAX_PENDING_FRAMES];

    nak_t   nak_queue[PICO_NAK_QUEUE_CAPACITY];
    uint8_t nak_queue_len;

    uint32_t frames_received;
    uint32_t frames_shown;
    uint32_t frames_dropped_late;
    uint32_t frames_dropped_queue_full;
    uint32_t naks_sent;
    uint32_t chunks_rejected; /* malformed or chunk_count-mismatched frame_buffer_submit_chunk() calls */
} frame_buffer_t;

void frame_buffer_init(frame_buffer_t *fb);

/* Queue one chunk of a frame. Once every chunk of `seq` has arrived, the
 * reassembled frame moves into the completed-frame slots - evicting the
 * single earliest-due occupied slot first if full (matches
 * network_driver.py's client-side "drop oldest" policy) rather than
 * declining, same as before - see docs/docs/pico-device.md for why this
 * device type never returns 429/refuses.
 *
 * Rejects (returns false, bumps fb->chunks_rejected, changes nothing else)
 * a chunk_count of 0, a chunk_index >= chunk_count, a payload_len that's 0
 * or too big for one chunk slot, or a chunk_count that disagrees with the
 * one an already-pending seq was first seen with. A duplicate chunk
 * (already received for this seq) is silently ignored (idempotent), not
 * rejected.
 *
 * Submitting a chunk for a seq not already pending may evict the single
 * earliest (by presentation_time_us) pending frame first, if the pending
 * pool (PICO_MAX_PENDING_FRAMES) is full. */
bool frame_buffer_submit_chunk(frame_buffer_t *fb, int64_t presentation_time_us, uint32_t seq,
                                uint8_t chunk_index, uint8_t chunk_count,
                                const uint8_t *payload, uint16_t payload_len);

/* Pop up to `max` pending NAKs into out_seq/out_chunk_index (parallel
 * arrays). Returns how many were popped. Call periodically from the UDP
 * server's poll loop (hw/udp_frame_server.c). */
uint8_t frame_buffer_take_naks(frame_buffer_t *fb, uint32_t *out_seq, uint8_t *out_chunk_index, uint8_t max);

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

#endif
