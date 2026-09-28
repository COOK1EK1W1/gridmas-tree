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

    /* nothing due on an empty buffer */
    assert(frame_buffer_poll(&fb, 1000, 250000, &out) == FRAME_BUFFER_NONE);
    assert(frame_buffer_free_slots(&fb) == PICO_FRAME_SLOT_COUNT);

    /* submit due at t=1000, poll before it's due -> NONE, poll once due -> READY */
    assert(frame_buffer_submit_frame(&fb, 1000, 1, payload, sizeof(payload)));
    assert(frame_buffer_depth(&fb) == 1);
    assert(frame_buffer_free_slots(&fb) == PICO_FRAME_SLOT_COUNT - 1);
    assert(frame_buffer_poll(&fb, 500, 250000, &out) == FRAME_BUFFER_NONE);
    assert(frame_buffer_poll(&fb, 1000, 250000, &out) == FRAME_BUFFER_READY);
    assert(out.seq == 1);
    assert(out.payload_len == sizeof(payload));
    assert(memcmp(out.payload, payload, sizeof(payload)) == 0);
    assert(frame_buffer_depth(&fb) == 0);
    assert(frame_buffer_poll(&fb, 1000, 250000, &out) == FRAME_BUFFER_NONE);

    /* a frame polled well past its presentation time is dropped as late, not shown */
    assert(frame_buffer_submit_frame(&fb, 1000, 2, payload, sizeof(payload)));
    assert(frame_buffer_poll(&fb, 1000 + 300000, 250000, &out) == FRAME_BUFFER_LATE);
    assert(fb.frames_dropped_late == 1);
    assert(frame_buffer_depth(&fb) == 0);

    /* earliest-due-first ordering, independent of submission order */
    assert(frame_buffer_submit_frame(&fb, 3000, 10, payload, sizeof(payload)));
    assert(frame_buffer_submit_frame(&fb, 2000, 11, payload, sizeof(payload)));
    assert(frame_buffer_submit_frame(&fb, 4000, 12, payload, sizeof(payload)));
    assert(frame_buffer_poll(&fb, 5000, 250000, &out) == FRAME_BUFFER_READY);
    assert(out.seq == 11); /* t=2000 was earliest */
    assert(frame_buffer_poll(&fb, 5000, 250000, &out) == FRAME_BUFFER_READY);
    assert(out.seq == 10);
    assert(frame_buffer_poll(&fb, 5000, 250000, &out) == FRAME_BUFFER_READY);
    assert(out.seq == 12);

    /* rejects a malformed payload length without touching state */
    assert(!frame_buffer_submit_frame(&fb, 1000, 99, payload, 0));
    assert(!frame_buffer_submit_frame(&fb, 1000, 99, payload, PICO_MAX_PIXELS_TOTAL * 3 + 1));
    assert(frame_buffer_depth(&fb) == 0);

    /* completed-slot eviction: submitting into a full buffer evicts the
     * earliest-due slot rather than declining */
    frame_buffer_init(&fb);
    for (int i = 0; i < PICO_FRAME_SLOT_COUNT; i++) {
        assert(frame_buffer_submit_frame(&fb, 10000 + i, 100 + i, payload, sizeof(payload)));
    }
    assert(frame_buffer_depth(&fb) == PICO_FRAME_SLOT_COUNT);
    assert(frame_buffer_free_slots(&fb) == 0);
    uint32_t dropped_before = fb.frames_dropped_queue_full;

    assert(frame_buffer_submit_frame(&fb, 10000 + PICO_FRAME_SLOT_COUNT, 999, payload, sizeof(payload)));
    assert(frame_buffer_depth(&fb) == PICO_FRAME_SLOT_COUNT); /* still full - oldest was evicted, not appended */
    assert(fb.frames_dropped_queue_full == dropped_before + 1);
    assert(frame_buffer_poll(&fb, 10000 + PICO_FRAME_SLOT_COUNT, 250000, &out) == FRAME_BUFFER_READY);
    assert(out.seq == 101); /* seq=100 (t=10000) was the evicted one; t=10001 survives as the new earliest */

    printf("frame_buffer: all tests passed\n");
    return 0;
}
