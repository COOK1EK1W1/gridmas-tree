#ifndef CORE_SNTP_OFFSET_H
#define CORE_SNTP_OFFSET_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Pure offset/delay math for a burst-of-exchanges SNTP client (see
 * docs/docs/time-sync.md). No Pico SDK / networking dependency - the caller
 * (hw/sntp_client.c) does the actual UDP exchange and hands the four
 * timestamps from each one here.
 *
 * Standard NTP four-timestamp exchange, all in microseconds since the Unix
 * epoch:
 *   t1 - this device sent the request (local clock, pre-correction)
 *   t2 - the server received it (server clock)
 *   t3 - the server sent its reply (server clock)
 *   t4 - this device received the reply (local clock, pre-correction)
 */

typedef struct {
    int64_t t1_us;
    int64_t t2_us;
    int64_t t3_us;
    int64_t t4_us;
} sntp_sample_t;

typedef struct {
    int64_t offset_us; /* add this to the local clock to correct it */
    int64_t delay_us;  /* round-trip delay estimate for this sample */
} sntp_result_t;

void sntp_offset_compute(const sntp_sample_t *sample, sntp_result_t *out);

/* From a burst of `count` samples, pick the one with the lowest round-trip
 * delay (low delay correlates with low path asymmetry, and therefore the
 * most trustworthy offset - Wi-Fi's asymmetric queuing/retries are exactly
 * what a single-exchange SNTP client is vulnerable to) and return its
 * offset/delay via *out. Returns false if count == 0. */
bool sntp_offset_best_of(const sntp_sample_t *samples, size_t count, sntp_result_t *out);

#endif
