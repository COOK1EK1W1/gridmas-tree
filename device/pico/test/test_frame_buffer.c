#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "core/frame_buffer.h"

int main(void) {
    frame_buffer_t fb;
    frame_buffer_init(&fb);

    uint8_t payload[9];
    memset(payload, 0x42, sizeof(payload));

    frame_t out;
    uint32_t nak_seq[8];
    uint8_t nak_chunk[8];

    /* nothing due on an empty buffer */
    assert(frame_buffer_poll(&fb, 1000, 250000, &out) == FRAME_BUFFER_NONE);

    /* single-chunk frame (chunk_index=0, chunk_count=1) submitted due at
     * t=1000, poll before it's due -> NONE, poll once due -> READY */
    assert(frame_buffer_submit_chunk(&fb, 1000, 1, 0, 1, payload, sizeof(payload)));
    assert(frame_buffer_depth(&fb) == 1);
    assert(frame_buffer_poll(&fb, 500, 250000, &out) == FRAME_BUFFER_NONE);
    assert(frame_buffer_poll(&fb, 1000, 250000, &out) == FRAME_BUFFER_READY);
    assert(out.seq == 1);
    assert(out.payload_len == sizeof(payload));
    assert(memcmp(out.payload, payload, sizeof(payload)) == 0);
    assert(frame_buffer_depth(&fb) == 0);
    assert(frame_buffer_poll(&fb, 1000, 250000, &out) == FRAME_BUFFER_NONE);

    /* a frame polled well past its presentation time is dropped as late, not shown */
    assert(frame_buffer_submit_chunk(&fb, 1000, 2, 0, 1, payload, sizeof(payload)));
    assert(frame_buffer_poll(&fb, 1000 + 300000, 250000, &out) == FRAME_BUFFER_LATE);
    assert(fb.frames_dropped_late == 1);
    assert(frame_buffer_depth(&fb) == 0);

    /* earliest-due-first ordering, independent of submission order */
    assert(frame_buffer_submit_chunk(&fb, 3000, 10, 0, 1, payload, sizeof(payload)));
    assert(frame_buffer_submit_chunk(&fb, 2000, 11, 0, 1, payload, sizeof(payload)));
    assert(frame_buffer_submit_chunk(&fb, 4000, 12, 0, 1, payload, sizeof(payload)));
    assert(frame_buffer_poll(&fb, 5000, 250000, &out) == FRAME_BUFFER_READY);
    assert(out.seq == 11); /* t=2000 was earliest */
    assert(frame_buffer_poll(&fb, 5000, 250000, &out) == FRAME_BUFFER_READY);
    assert(out.seq == 10);
    assert(frame_buffer_poll(&fb, 5000, 250000, &out) == FRAME_BUFFER_READY);
    assert(out.seq == 12);

    /* rejects a malformed payload length without touching state */
    assert(!frame_buffer_submit_chunk(&fb, 1000, 99, 0, 1, payload, 0));
    assert(!frame_buffer_submit_chunk(&fb, 1000, 99, 0, 1, payload, PICO_PIXELS_PER_CHUNK * 3 + 1));
    /* rejects a malformed chunk_index/chunk_count */
    assert(!frame_buffer_submit_chunk(&fb, 1000, 99, 0, 0, payload, sizeof(payload)));
    assert(!frame_buffer_submit_chunk(&fb, 1000, 99, 2, 2, payload, sizeof(payload)));
    assert(!frame_buffer_submit_chunk(&fb, 1000, 99, 0, PICO_MAX_CHUNKS_PER_FRAME + 1, payload, sizeof(payload)));
    assert(frame_buffer_depth(&fb) == 0);

    /* multi-chunk reassembly, out of order - the frame isn't "received"
     * until every chunk has arrived. Only the *last* chunk of a frame may
     * be shorter than a full chunk (see docs/docs/network-pixel-protocol.md
     * - ceil-division chunking guarantees every earlier chunk is exactly
     * PICO_PIXELS_PER_CHUNK*3 bytes), so chunk 0 here (not the last, since
     * chunk_count=2) must be full-size for the fixed-offset reassembly to
     * land chunk 1 contiguously right after it. */
    uint8_t payload0[PICO_PIXELS_PER_CHUNK * 3];
    memset(payload0, 0x99, sizeof(payload0));
    assert(frame_buffer_submit_chunk(&fb, 6000, 20, 1, 2, payload, 4)); /* chunk 1 (last, short) first */
    assert(frame_buffer_depth(&fb) == 0);                              /* still incomplete */
    assert(frame_buffer_submit_chunk(&fb, 6000, 20, 0, 2, payload0, sizeof(payload0)));
    assert(frame_buffer_depth(&fb) == 1); /* now complete */
    assert(frame_buffer_poll(&fb, 6000, 250000, &out) == FRAME_BUFFER_READY);
    assert(out.seq == 20);
    assert(out.payload_len == sizeof(payload0) + 4);
    assert(memcmp(out.payload, payload0, sizeof(payload0)) == 0);             /* chunk 0 at offset 0 */
    assert(memcmp(out.payload + sizeof(payload0), payload, 4) == 0);          /* chunk 1 right after it */

    /* a chunk_count mismatch against an already-pending seq is rejected,
     * not trusted - otherwise it could either wedge the frame (Python side)
     * or complete it prematurely with chunks still missing (this bug was
     * present here until fixed: the completeness check used the mismatched
     * per-call chunk_count instead of the pending frame's own) */
    assert(frame_buffer_submit_chunk(&fb, 6500, 25, 0, 2, payload0, sizeof(payload0))); /* chunk 0 of 2 */
    assert(!frame_buffer_submit_chunk(&fb, 6500, 25, 1, 3, payload, 4));                /* claims 3 chunks now - rejected */
    assert(frame_buffer_depth(&fb) == 0);                                              /* not completed */
    assert(frame_buffer_submit_chunk(&fb, 6500, 25, 1, 2, payload, 4));                 /* correct chunk_count */
    assert(frame_buffer_depth(&fb) == 1);
    assert(frame_buffer_poll(&fb, 6500, 250000, &out) == FRAME_BUFFER_READY);
    assert(out.seq == 25);
    assert(out.payload_len == sizeof(payload0) + 4);

    /* duplicate chunk is ignored, not double-counted */
    assert(frame_buffer_submit_chunk(&fb, 7000, 21, 0, 2, payload0, sizeof(payload0)));
    assert(frame_buffer_submit_chunk(&fb, 7000, 21, 0, 2, payload0, sizeof(payload0))); /* dup */
    assert(frame_buffer_depth(&fb) == 0); /* still waiting on chunk 1 */
    assert(frame_buffer_submit_chunk(&fb, 7000, 21, 1, 2, payload, 4));
    assert(frame_buffer_depth(&fb) == 1);
    assert(frame_buffer_poll(&fb, 7000, 250000, &out) == FRAME_BUFFER_READY);
    assert(out.payload_len == sizeof(payload0) + 4); /* not doubled */

    /* stall detection: seq=30 missing chunk 1; PICO_STALL_AFTER later
     * (single-chunk, immediately-complete) frames later, exactly one NAK
     * for (30, 1) should be queued - and not re-queued by further later
     * frames completing */
    assert(frame_buffer_submit_chunk(&fb, 8000, 30, 0, 2, payload0, sizeof(payload0))); /* chunk 0, full-size */
    assert(frame_buffer_take_naks(&fb, nak_seq, nak_chunk, 8) == 0);
    for (int i = 0; i < PICO_STALL_AFTER; i++) {
        assert(frame_buffer_submit_chunk(&fb, 8001, 31 + i, 0, 1, payload, sizeof(payload)));
    }
    uint8_t n = frame_buffer_take_naks(&fb, nak_seq, nak_chunk, 8);
    assert(n == 1);
    assert(nak_seq[0] == 30 && nak_chunk[0] == 1);
    assert(fb.naks_sent == 1);
    /* more later frames completing must not re-NAK the same gap */
    for (int i = 0; i < 3; i++) {
        assert(frame_buffer_submit_chunk(&fb, 8002, 40 + i, 0, 1, payload, sizeof(payload)));
    }
    assert(frame_buffer_take_naks(&fb, nak_seq, nak_chunk, 8) == 0);
    /* the NAK'd chunk can still arrive late and complete the frame */
    assert(frame_buffer_submit_chunk(&fb, 8000, 30, 1, 2, payload, 4));
    bool found_30 = false;
    for (int i = 0; i < 200 && frame_buffer_depth(&fb) > 0; i++) {
        if (frame_buffer_poll(&fb, 999999, 999999999, &out) == FRAME_BUFFER_READY && out.seq == 30) {
            found_30 = true;
        }
    }
    assert(found_30);

    /* pending-pool eviction: filling PICO_MAX_PENDING_FRAMES with
     * multi-chunk (still-incomplete) frames evicts the earliest-due one
     * rather than growing */
    frame_buffer_init(&fb);
    for (int i = 0; i < PICO_MAX_PENDING_FRAMES; i++) {
        assert(frame_buffer_submit_chunk(&fb, 9000 + i, 200 + i, 0, 2, payload, 4)); /* only chunk 0 - stays pending */
    }
    uint32_t pending_dropped_before = fb.frames_dropped_queue_full;
    assert(frame_buffer_submit_chunk(&fb, 9000 + PICO_MAX_PENDING_FRAMES, 999, 0, 2, payload, 4));
    assert(fb.frames_dropped_queue_full == pending_dropped_before + 1);
    /* the evicted one (seq=200, earliest t) can no longer be completed -
     * finishing it now starts a *new* pending frame instead */
    assert(frame_buffer_submit_chunk(&fb, 9000, 200, 1, 2, payload, 4));
    assert(frame_buffer_depth(&fb) == 0); /* treated as a fresh, still-incomplete frame */

    /* completed-slot eviction, still works the same as before, now via the
     * chunked API */
    frame_buffer_init(&fb);
    for (int i = 0; i < PICO_FRAME_SLOT_COUNT; i++) {
        assert(frame_buffer_submit_chunk(&fb, 10000 + i, 100 + i, 0, 1, payload, sizeof(payload)));
    }
    assert(frame_buffer_depth(&fb) == PICO_FRAME_SLOT_COUNT);
    uint32_t dropped_before = fb.frames_dropped_queue_full;

    assert(frame_buffer_submit_chunk(&fb, 10000 + PICO_FRAME_SLOT_COUNT, 999, 0, 1, payload, sizeof(payload)));
    assert(frame_buffer_depth(&fb) == PICO_FRAME_SLOT_COUNT); /* still full - oldest was evicted, not appended */
    assert(fb.frames_dropped_queue_full == dropped_before + 1);
    assert(frame_buffer_poll(&fb, 10000 + PICO_FRAME_SLOT_COUNT, 250000, &out) == FRAME_BUFFER_READY);
    assert(out.seq == 101); /* seq=100 (t=10000) was the evicted one; t=10001 survives as the new earliest */

    printf("frame_buffer: all tests passed\n");
    return 0;
}
