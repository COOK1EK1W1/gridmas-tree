#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

#include "core/sntp_offset.h"

static bool close_enough(int64_t a, int64_t b, int64_t tol) {
    int64_t d = a - b;
    if (d < 0) d = -d;
    return d <= tol;
}

int main(void) {
    /* symmetric path, server 100ms ahead of us, 10ms round-trip delay */
    sntp_sample_t s = {
        .t1_us = 1000000,
        .t2_us = 1000000 + 100000 + 5000,
        .t3_us = 1000000 + 100000 + 5000,
        .t4_us = 1000000 + 10000,
    };
    sntp_result_t r;
    sntp_offset_compute(&s, &r);
    assert(close_enough(r.offset_us, 100000, 1));
    assert(close_enough(r.delay_us, 10000, 1));

    /* burst of 3 samples, true offset = +100000us in every case, but only
     * the symmetric-path ("clean") sample computes it exactly right - the
     * other two have asymmetric up/down delays (as Wi-Fi jitter causes) and
     * so compute a measurably wrong offset despite a real server 100ms ahead.
     * best_of() must pick the lowest-delay (clean) sample, not just any one. */
    sntp_sample_t burst[3] = {
        {.t1_us = 0, .t2_us = 170000, .t3_us = 170000, .t4_us = 80000},  /* noisy: 70ms up / 10ms down, 80ms rtt */
        {.t1_us = 0, .t2_us = 102500, .t3_us = 102500, .t4_us = 5000},   /* clean: 2.5ms/2.5ms, 5ms rtt */
        {.t1_us = 0, .t2_us = 120000, .t3_us = 120000, .t4_us = 30000},  /* medium: 20ms/10ms, 30ms rtt */
    };
    sntp_result_t best;
    assert(sntp_offset_best_of(burst, 3, &best));
    assert(close_enough(best.delay_us, 5000, 1));
    assert(close_enough(best.offset_us, 100000, 1)); /* the clean sample's offset, not the noisy ones' */

    assert(!sntp_offset_best_of(NULL, 0, &best));

    printf("sntp_offset: all tests passed\n");
    return 0;
}
