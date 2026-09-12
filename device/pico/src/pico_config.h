#ifndef PICO_CONFIG_H
#define PICO_CONFIG_H

/* Tunable constants for this device type. Named and centralised here rather
 * than scattered through the code (per the design discussion) - see
 * docs/docs/pico-device.md for the reasoning behind each of these. Every
 * physical Pico runs the exact same firmware, so these apply fleet-wide, not
 * per-device.
 */

/* -- Output -- */
#define PICO_NUM_LED_PINS 2         /* fixed pins, identical wiring on every board - see hw/ws2812_output.c */
#define PICO_MAX_PIXELS_PER_PIN 500 /* WS2812 timing ceiling for sustained 45fps on one data line */
#define PICO_MAX_PIXELS_TOTAL (PICO_NUM_LED_PINS * PICO_MAX_PIXELS_PER_PIN)

/* -- Frame buffering (mirrors device/common/scheduler.py's capacity/late_grace) -- */
#define PICO_FRAME_SLOT_COUNT 90  /* ~2s at 45fps, matching the controller's PREROLL+BUFFER lookahead */
#define PICO_LATE_GRACE_US 250000 /* drop, don't show, a frame shown later than this past its due time */

/* -- Chunking (mirrors backend/network_driver.py's PIXELS_PER_CHUNK) - see
 * docs/docs/network-pixel-protocol.md for the wire format this sizes. */
#define PICO_PIXELS_PER_CHUNK 480
#define PICO_MAX_CHUNKS_PER_FRAME (((PICO_MAX_PIXELS_TOTAL) + (PICO_PIXELS_PER_CHUNK) - 1) / (PICO_PIXELS_PER_CHUNK))

/* -- Gap detection / retransmission (docs/docs/network-pixel-protocol.md
 * "Gap detection and retransmission") --
 *
 * PICO_MAX_PENDING_FRAMES is deliberately much smaller than
 * PICO_FRAME_SLOT_COUNT: each pending slot pre-allocates a full
 * PICO_MAX_PIXELS_TOTAL*3-byte payload buffer for reassembly, and in
 * practice only a handful of frames are ever mid-reassembly at once (a
 * frame is at most PICO_MAX_CHUNKS_PER_FRAME chunks, which normally
 * resolves in well under one frame interval). Doubling frame_buffer_t's
 * footprint to match PICO_FRAME_SLOT_COUNT here isn't worth the SRAM. */
#define PICO_STALL_AFTER 3        /* later frames completed before a gap is NAK'd */
#define PICO_MAX_PENDING_FRAMES 8 /* frames mid-reassembly at once */
#define PICO_NAK_QUEUE_CAPACITY (PICO_MAX_PENDING_FRAMES * PICO_MAX_CHUNKS_PER_FRAME)

/* -- Time sync -- */
#define PICO_SNTP_RESYNC_INTERVAL_S 300 /* 5 minutes - starting point, tune against measured drift */
#define PICO_SNTP_BURST_SAMPLES 6       /* exchanges per resync; lowest-round-trip-delay one wins */
#define PICO_SNTP_SAMPLE_TIMEOUT_MS 1000

/* Not a secret - the controller's LAN IP, the same one GRIDMAS_DEVICE_ADDRESS
 * points NetworkPixelDriver at, now also running chronyd (see
 * docs/docs/time-sync.md). Fill in for your network. */
#define CONTROLLER_TIME_SERVER_IP "192.168.1.141"

/* -- Networking --
 *
 * PICO_HTTP_PORT is used for both transports: the TCP listener for
 * GET /status and POST /clear (hw/http_server.c), and the UDP socket for
 * frame data + NAKs (hw/udp_frame_server.c) - TCP and UDP port numbers are
 * independent namespaces, and the controller likewise reuses one port
 * number for both (see backend/network_driver.py). */
#define PICO_HTTP_PORT 8420
#define PICO_MAX_CONCURRENT_CONNS 4 /* keep-alive HTTP connections accepted at once (status/clear only -
                                     * frame data no longer goes over TCP) */

/* -- Resilience --
 *
 * PICO_WATCHDOG_TIMEOUT_MS must exceed the longest single blocking call this
 * firmware makes that it cannot feed the watchdog *during* - that's each
 * individual Wi-Fi connect attempt (hw/wifi.c's WIFI_CONNECT_ATTEMPT_TIMEOUT_MS,
 * a single blocking SDK call). 8000ms sits just under the RP2350 hardware
 * watchdog's ~8.3s single-stage ceiling, comfortably above a 6000ms connect
 * attempt. Get this wrong in the other direction (watchdog shorter than the
 * attempt timeout) and the device boot-loops forever, since nothing can feed
 * the watchdog mid-call - ask me how I know. */
#define PICO_WATCHDOG_TIMEOUT_MS 8000
#define PICO_WIFI_LOSS_REBOOT_TIMEOUT_MS 30000 /* only armed once this boot has associated at least once */

#endif
