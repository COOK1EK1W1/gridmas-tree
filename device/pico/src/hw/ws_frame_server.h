#ifndef HW_WS_FRAME_SERVER_H
#define HW_WS_FRAME_SERVER_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "lwip/tcp.h"

#include "pico/critical_section.h"

#include "core/frame_buffer.h"

/* WebSocket side of docs/docs/network-pixel-protocol.md's data plane: the
 * controller connects in as the WS client, this device is the WS server.
 * There's no listener here - hw/http_server.c owns the device's one TCP
 * port, and hands a connection over via ws_frame_server_adopt() once its
 * request turns out to be a WebSocket upgrade. From then on this module owns
 * that pcb's callbacks.
 *
 * Only one controller connects at a time - a new WS connection replaces
 * whatever was previously connected. Runs entirely from lwIP's callback
 * context on core0 - see main.c. Frame submission crosses into the
 * frame_buffer shared with core1 via `fb_lock`, the same critical_section_t
 * main.c hands to http_server_init(). */

void ws_frame_server_init(frame_buffer_t *fb, critical_section_t *fb_lock);

/* Takes over `pcb` (whose HTTP request was a GET carrying Sec-WebSocket-Key
 * `ws_key`): sends the 101 Switching Protocols response, installs this
 * module's lwIP callbacks, and sends the initial CREDIT snapshot. Must be
 * called from lwIP callback context. Returns false (without touching the
 * pcb's callbacks) if the handshake response couldn't be queued - the caller
 * still owns the pcb then and should close it. */
bool ws_frame_server_adopt(struct tcp_pcb *pcb, const char *ws_key);

/* Feeds WS bytes that arrived in the same segment as the upgrade request,
 * after its headers - hw/http_server.c's recv_cb already has them in hand.
 * Returns false if this closed the connection (the caller must not touch the
 * pcb again). */
bool ws_frame_server_feed(const uint8_t *data, size_t len);

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
