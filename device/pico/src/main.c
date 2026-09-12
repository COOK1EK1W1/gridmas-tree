#include <stdio.h>

#include "hardware/watchdog.h"
#include "pico/critical_section.h"
#include "pico/multicore.h"
#include "pico/stdlib.h"

#include "core/frame_buffer.h"
#include "hw/http_server.h"
#include "hw/sntp_client.h"
#include "hw/udp_frame_server.h"
#include "hw/wifi.h"
#include "hw/ws2812_output.h"
#include "pico_config.h"

/* See docs/docs/pico-device.md for the full design this implements. */

static frame_buffer_t g_frame_buffer;

/* frame_buffer.c is not thread/core-safe on its own (see its header
 * comment). This is the one critical_section_t protecting g_frame_buffer,
 * shared by core1 (below) and both core0 users (http_server.c's /clear,
 * udp_frame_server.c's frame submission and NAK draining) - each of those
 * creating its own critical_section_t instead would claim separate
 * hardware spinlocks that don't exclude each other at all. */
static critical_section_t g_frame_buffer_lock;

/* Written by core1 every loop iteration, read by core0 to gate the hardware
 * watchdog feed - see below. A single shared watchdog_update() call fed from
 * either core alone would only ever detect BOTH cores hanging at once; this
 * makes core0's feed depend on core1 also proving it's alive recently, so
 * either core stalling stops the feed and the watchdog reboots the board. */
static volatile uint64_t g_core1_alive_us = 0;
#define CORE1_STALL_THRESHOLD_US 500000 /* generous vs core1's ~1ms tick */

/* core1: frame scheduling + PIO/DMA output timing. Kept apart from
 * networking so Wi-Fi/HTTP jitter can never delay a due frame, and a strip
 * render never blocks frame reception - same reasoning as the real device's
 * scheduler thread (device/common/scheduler.py).
 *
 * Deliberately no printf()/stdio calls anywhere in this function or anything
 * it calls - USB CDC stdio can stall, and this loop's whole job is precise,
 * jitter-free timing. All logging lives on core0 (main()'s loop, wifi.c,
 * http_server.c) instead. */
static void core1_entry(void) {
    while (true) {
        g_core1_alive_us = time_us_64();

        int64_t now_us = (int64_t)time_us_64() + sntp_client_offset_us();

        frame_t frame;
        critical_section_enter_blocking(&g_frame_buffer_lock);
        frame_buffer_poll_result_t r = frame_buffer_poll(&g_frame_buffer, now_us, PICO_LATE_GRACE_US, &frame);
        critical_section_exit(&g_frame_buffer_lock);
        if (r == FRAME_BUFFER_READY) {
            ws2812_output_show(frame.payload, frame.payload_len);
        }
        /* FRAME_BUFFER_NONE / FRAME_BUFFER_LATE: nothing to draw this tick -
         * per docs/docs/pico-device.md Q18, hold whatever was last shown
         * rather than auto-blanking on an empty/stale buffer */

        sleep_us(1000); /* well under the ~22ms frame interval at 45fps */
    }
}

int main(void) {
    stdio_init_all();

    bool rebooted_by_watchdog = watchdog_caused_reboot();
    /* armed before wifi_init_and_connect_blocking() deliberately - see
     * pico_config.h's PICO_WATCHDOG_TIMEOUT_MS comment and
     * hw/wifi.c's WIFI_CONNECT_ATTEMPT_TIMEOUT_MS: that function's own retry
     * loop feeds this watchdog between attempts, so it must already be armed
     * by the time it's called. */
    watchdog_enable(PICO_WATCHDOG_TIMEOUT_MS, true);

    ws2812_output_init();
    ws2812_output_blank(); /* blank on boot only - see docs/docs/pico-device.md Q18 */

    frame_buffer_init(&g_frame_buffer);
    critical_section_init(&g_frame_buffer_lock);

    printf("gridmas-pico: booting%s\n", rebooted_by_watchdog ? " (after a watchdog reboot)" : "");

    wifi_init_and_connect_blocking();
    watchdog_update();

    sntp_client_init(CONTROLLER_TIME_SERVER_IP);
    http_server_init(&g_frame_buffer, &g_frame_buffer_lock);
    udp_frame_server_init(&g_frame_buffer, &g_frame_buffer_lock);

    multicore_launch_core1(core1_entry);

    absolute_time_t next_resync = get_absolute_time(); /* sync immediately on boot */

    while (true) {
        wifi_poll();
        http_server_poll();
        udp_frame_server_poll();

        if (!sntp_client_burst_in_progress() && absolute_time_diff_us(get_absolute_time(), next_resync) <= 0) {
            sntp_client_start_sync();
            next_resync = make_timeout_time_ms(PICO_SNTP_RESYNC_INTERVAL_S * 1000);
        }
        sntp_client_poll();
        if (sntp_client_burst_done()) {
            bool was_synced = sntp_client_synced();
            sntp_client_finish_burst();
            http_server_set_synced(sntp_client_synced(), sntp_client_offset_us(), sntp_client_last_delay_us());
            udp_frame_server_set_synced(sntp_client_synced());

            if (!was_synced && sntp_client_synced()) {
                printf("gridmas-pico: first time sync complete - now accepting frames\n");
            }
            if (sntp_client_synced()) {
                /* logged every resync (every PICO_SNTP_RESYNC_INTERVAL_S), not
                 * just the first - watch this drift over time to judge
                 * whether the interval needs tightening, per
                 * docs/docs/time-sync.md */
                printf("gridmas-pico: sync ok, offset %lldus, delay %lldus\n",
                       (long long)sntp_client_offset_us(), (long long)sntp_client_last_delay_us());
            } else {
                printf("gridmas-pico: sync attempt got no replies - %s\n",
                       was_synced ? "keeping the previous offset" : "still not accepting frames");
            }
        }

        /* feed the watchdog only while core1 has also proven it's alive
         * recently - see g_core1_alive_us above */
        if (time_us_64() - g_core1_alive_us < CORE1_STALL_THRESHOLD_US) {
            watchdog_update();
        }

        sleep_ms(1);
    }

    return 0;
}
