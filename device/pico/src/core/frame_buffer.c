#include "core/frame_buffer.h"

#include <string.h>

void frame_buffer_init(frame_buffer_t *fb) {
    memset(fb, 0, sizeof(*fb));
}

static int find_free_slot(const frame_buffer_t *fb) {
    for (int i = 0; i < PICO_FRAME_SLOT_COUNT; i++) {
        if (!fb->occupied[i]) return i;
    }
    return -1;
}

/* Smallest presentation_time among occupied slots - this is both "the next
 * one due" (for poll) and "the one submitted furthest in the past relative
 * to what's still buffered" (for eviction) - the same slot serves both. */
static int find_earliest_slot(const frame_buffer_t *fb) {
    int earliest = -1;
    for (int i = 0; i < PICO_FRAME_SLOT_COUNT; i++) {
        if (!fb->occupied[i]) continue;
        if (earliest < 0 || fb->slots[i].presentation_time_us < fb->slots[earliest].presentation_time_us) {
            earliest = i;
        }
    }
    return earliest;
}

bool frame_buffer_submit_frame(frame_buffer_t *fb, int64_t presentation_time_us, uint32_t seq,
                                const uint8_t *payload, uint16_t payload_len) {
    if (payload_len == 0 || payload_len > PICO_MAX_PIXELS_TOTAL * 3) {
        fb->frames_rejected_bad_payload++;
        return false;
    }

    int slot = find_free_slot(fb);
    if (slot < 0) {
        slot = find_earliest_slot(fb);
        fb->frames_dropped_queue_full++;
    }

    frame_t *f = &fb->slots[slot];
    f->presentation_time_us = presentation_time_us;
    f->seq = seq;
    f->payload_len = payload_len;
    memcpy(f->payload, payload, payload_len);
    fb->occupied[slot] = true;
    fb->frames_received++;
    return true;
}

frame_buffer_poll_result_t frame_buffer_poll(frame_buffer_t *fb, int64_t now_us,
                                              int64_t late_grace_us, frame_t *out) {
    int slot = find_earliest_slot(fb);
    if (slot < 0) return FRAME_BUFFER_NONE;

    int64_t t = fb->slots[slot].presentation_time_us;
    if (t > now_us) return FRAME_BUFFER_NONE; /* earliest isn't due yet */

    fb->occupied[slot] = false;

    if (now_us - t > late_grace_us) {
        fb->frames_dropped_late++;
        return FRAME_BUFFER_LATE;
    }

    *out = fb->slots[slot];
    fb->frames_shown++;
    return FRAME_BUFFER_READY;
}

uint32_t frame_buffer_depth(const frame_buffer_t *fb) {
    uint32_t n = 0;
    for (int i = 0; i < PICO_FRAME_SLOT_COUNT; i++) {
        if (fb->occupied[i]) n++;
    }
    return n;
}

uint32_t frame_buffer_free_slots(const frame_buffer_t *fb) {
    return (uint32_t)PICO_FRAME_SLOT_COUNT - frame_buffer_depth(fb);
}
