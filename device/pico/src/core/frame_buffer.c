#include "core/frame_buffer.h"

#include <string.h>

void frame_buffer_init(frame_buffer_t *fb) {
    memset(fb, 0, sizeof(*fb));
}

/* -- Completed-frame slots (played back by frame_buffer_poll) -- */

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

/* -- Pending (mid-reassembly) frames -- */

static int find_pending_by_seq(const frame_buffer_t *fb, uint32_t seq) {
    for (int i = 0; i < PICO_MAX_PENDING_FRAMES; i++) {
        if (fb->pending[i].in_use && fb->pending[i].seq == seq) return i;
    }
    return -1;
}

static int find_free_pending_slot(const frame_buffer_t *fb) {
    for (int i = 0; i < PICO_MAX_PENDING_FRAMES; i++) {
        if (!fb->pending[i].in_use) return i;
    }
    return -1;
}

static int find_earliest_pending_slot(const frame_buffer_t *fb) {
    int earliest = -1;
    for (int i = 0; i < PICO_MAX_PENDING_FRAMES; i++) {
        if (!fb->pending[i].in_use) continue;
        if (earliest < 0 ||
            fb->pending[i].presentation_time_us < fb->pending[earliest].presentation_time_us) {
            earliest = i;
        }
    }
    return earliest;
}

static uint32_t chunk_mask(uint8_t chunk_count) {
    return (chunk_count >= 32) ? 0xFFFFFFFFu : ((1u << chunk_count) - 1u);
}

/* A frame just finished reassembling: move it into the completed-frame
 * slots (evicting the earliest-due occupied slot first if full, same
 * policy as before), free its pending slot, and - since a later frame just
 * completed - give every still-pending, earlier-seq'd frame one more
 * "stalled" strike, NAK'ing any that just crossed PICO_STALL_AFTER for the
 * chunks they're still missing (and haven't already been NAK'd for). */
static void complete_pending(frame_buffer_t *fb, pending_frame_t *p) {
    int slot = find_free_slot(fb);
    if (slot < 0) {
        slot = find_earliest_slot(fb);
        fb->frames_dropped_queue_full++;
    }

    frame_t *f = &fb->slots[slot];
    f->presentation_time_us = p->presentation_time_us;
    f->seq = p->seq;
    f->payload_len = p->total_len;
    memcpy(f->payload, p->payload, p->total_len);
    fb->occupied[slot] = true;
    fb->frames_received++;

    uint32_t completed_seq = p->seq;
    p->in_use = false;

    for (int i = 0; i < PICO_MAX_PENDING_FRAMES; i++) {
        pending_frame_t *other = &fb->pending[i];
        if (!other->in_use || other->seq >= completed_seq) continue;

        other->stall_count++;
        if (other->stall_count < PICO_STALL_AFTER) continue;

        uint32_t missing = chunk_mask(other->chunk_count) & ~other->received_mask & ~other->naked_mask;
        for (uint8_t c = 0; c < other->chunk_count; c++) {
            if (!(missing & (1u << c))) continue;
            other->naked_mask |= (1u << c);
            if (fb->nak_queue_len < PICO_NAK_QUEUE_CAPACITY) {
                fb->nak_queue[fb->nak_queue_len].seq = other->seq;
                fb->nak_queue[fb->nak_queue_len].chunk_index = c;
                fb->nak_queue_len++;
                fb->naks_sent++;
            }
            /* else: NAK queue momentarily full - this gap just falls
             * through to the ordinary late-grace drop, same as any other
             * loss the retransmit path doesn't catch. */
        }
    }
}

bool frame_buffer_submit_chunk(frame_buffer_t *fb, int64_t presentation_time_us, uint32_t seq,
                                uint8_t chunk_index, uint8_t chunk_count,
                                const uint8_t *payload, uint16_t payload_len) {
    if (chunk_count == 0 || chunk_count > PICO_MAX_CHUNKS_PER_FRAME || chunk_index >= chunk_count) {
        fb->chunks_rejected++;
        return false;
    }
    if (payload_len == 0 || payload_len > PICO_PIXELS_PER_CHUNK * 3) {
        fb->chunks_rejected++;
        return false;
    }

    int idx = find_pending_by_seq(fb, seq);
    if (idx < 0) {
        idx = find_free_pending_slot(fb);
        if (idx < 0) {
            idx = find_earliest_pending_slot(fb);
            fb->frames_dropped_queue_full++;
        }
        memset(&fb->pending[idx], 0, sizeof(fb->pending[idx]));
        fb->pending[idx].in_use = true;
        fb->pending[idx].seq = seq;
        fb->pending[idx].presentation_time_us = presentation_time_us;
        fb->pending[idx].chunk_count = chunk_count;
    } else if (fb->pending[idx].chunk_count != chunk_count) {
        fb->chunks_rejected++;
        return false; /* inconsistent chunk_count for an already-pending seq - ignore */
    }

    pending_frame_t *p = &fb->pending[idx];
    uint32_t bit = 1u << chunk_index;
    if (p->received_mask & bit) {
        return true; /* duplicate chunk - idempotent, ignore (see protocol doc) */
    }

    size_t offset = (size_t)chunk_index * ((size_t)PICO_PIXELS_PER_CHUNK * 3);
    if (offset + payload_len > sizeof(p->payload)) {
        fb->chunks_rejected++;
        return false; /* would overflow the fixed payload buffer */
    }

    memcpy(p->payload + offset, payload, payload_len);
    p->received_mask |= bit;
    p->total_len += payload_len;

    /* p->chunk_count (established when this pending frame was first seen),
     * not the chunk_count parameter above - they're guaranteed equal here
     * (the mismatch case already returned), but p->chunk_count is the one
     * that's actually correct to complete against. */
    if (p->received_mask != chunk_mask(p->chunk_count)) {
        return true; /* still incomplete */
    }

    complete_pending(fb, p);
    return true;
}

uint8_t frame_buffer_take_naks(frame_buffer_t *fb, uint32_t *out_seq, uint8_t *out_chunk_index, uint8_t max) {
    uint8_t n = fb->nak_queue_len < max ? fb->nak_queue_len : max;
    for (uint8_t i = 0; i < n; i++) {
        out_seq[i] = fb->nak_queue[i].seq;
        out_chunk_index[i] = fb->nak_queue[i].chunk_index;
    }
    uint8_t remaining = fb->nak_queue_len - n;
    memmove(fb->nak_queue, fb->nak_queue + n, remaining * sizeof(fb->nak_queue[0]));
    fb->nak_queue_len = remaining;
    return n;
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
