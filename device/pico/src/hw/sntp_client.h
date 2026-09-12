#ifndef HW_SNTP_CLIENT_H
#define HW_SNTP_CLIENT_H

#include <stdbool.h>
#include <stdint.h>

/* Real NTP-wire-format client (interoperable with any NTP/SNTP server; in
 * practice pointed at the chronyd instance on the controller - see
 * docs/docs/time-sync.md) doing a burst of exchanges per resync and keeping
 * the lowest-round-trip-delay sample (core/sntp_offset.c).
 *
 * This is NOT lwIP's bundled apps/sntp client - that module applies a single
 * exchange's result directly and doesn't expose the raw per-exchange
 * timestamps a burst-and-select strategy needs, so this talks the same wire
 * protocol via lwIP's raw UDP API instead (see docs/docs/pico-device.md,
 * the "single exchange vs burst" discussion).
 *
 * NOT thread/core-safe - call only from core0 (see main.c).
 */

void sntp_client_init(const char *server_ip);

/* Starts one burst-and-resync cycle. Non-blocking - call sntp_client_poll()
 * regularly afterwards to drive it. */
void sntp_client_start_sync(void);
bool sntp_client_burst_in_progress(void);

void sntp_client_poll(void);

/* True once the current burst has either collected PICO_SNTP_BURST_SAMPLES
 * replies or given up after too many failed attempts. Call
 * sntp_client_finish_burst() once this is true to apply the result (if any
 * samples came back) and end the burst. */
bool sntp_client_burst_done(void);
void sntp_client_finish_burst(void);

bool sntp_client_synced(void);
int64_t sntp_client_offset_us(void);    /* add to time_us_64() for corrected unix-epoch microseconds */
int64_t sntp_client_last_delay_us(void);

#endif
