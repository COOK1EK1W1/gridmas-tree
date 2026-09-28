#include "core/sntp_offset.h"

void sntp_offset_compute(const sntp_sample_t *s, sntp_result_t *out) {
    out->offset_us = ((s->t2_us - s->t1_us) + (s->t3_us - s->t4_us)) / 2;
    out->delay_us = (s->t4_us - s->t1_us) - (s->t3_us - s->t2_us);
}

bool sntp_offset_best_of(const sntp_sample_t *samples, size_t count, sntp_result_t *out) {
    if (count == 0) return false;

    sntp_result_t best;
    sntp_offset_compute(&samples[0], &best);

    for (size_t i = 1; i < count; i++) {
        sntp_result_t r;
        sntp_offset_compute(&samples[i], &r);
        if (r.delay_us < best.delay_us) best = r;
    }

    *out = best;
    return true;
}
