#ifndef HW_WS_FRAME_SERVER_H
#define HW_WS_FRAME_SERVER_H

#include <stdbool.h>
#include <stdint.h>

#include "pico/critical_section.h"

#include "core/frame_buffer.h"

/* WebSocket side of docs/docs/network-pixel-protocol.md's data plane: the
 * controller connects in as the WS client, this device is the WS server, on
 * its own TCP listener (PICO_WS_PORT) separate from hw/http_server.c's
 * GET /status and POST /clear. Replaces the old UDP+NAK data plane entirely
 * - TCP's reliable, ordered delivery (under WS) removes the need for
 * chunking, gap detection, and retransmission.
 *
 * Only one controller connects at a time - a new WS connection replaces
 * whatever was previously connected. Runs entirely from lwIP's callback
 * context on core0 - see main.c. Frame submission crosses into the
 * frame_buffer shared with core1 via `fb_lock`, the same critical_section_t
 * main.c hands to http_server_init(). */

void ws_frame_server_init(frame_buffer_t *fb, critical_section_t *fb_lock);

/* Call from core0's loop alongside wifi_poll()/http_server_poll() - sends a
 * CREDIT snapshot (frame_buffer_free_slots()) to the connected controller,
 * if any, whenever it's changed since the last send or a heartbeat interval
 * has elapsed, so silence on the connection is itself meaningful. */
void ws_frame_server_poll(void);

/* Gates inbound frames the same way the old UDP server did: before the
 * first successful SNTP sync, FRAME messages are received but discarded
 * rather than submitted, since presentation_time_us can't be scheduled
 * against an unsynced clock. */
void ws_frame_server_set_synced(bool synced);

/* Count of FRAME messages discarded so far because they arrived before the
 * first SNTP sync completed - see ws_frame_server_set_synced(). Surfaced in
 * GET /status and the periodic core0 log line (main.c) as a diagnostic: a
 * controller that's connected and streaming but a device stuck unsynced
 * (bad CONTROLLER_TIME_SERVER_IP, chronyd not running on the controller,
 * blocked NTP port) looks identical to "no LEDs" without this. */
uint32_t ws_frame_server_frames_dropped_presync(void);

#endif
