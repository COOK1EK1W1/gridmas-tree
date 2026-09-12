#ifndef HW_UDP_FRAME_SERVER_H
#define HW_UDP_FRAME_SERVER_H

#include <stdbool.h>

#include "pico/critical_section.h"

#include "core/frame_buffer.h"

/* UDP side of docs/docs/network-pixel-protocol.md's data plane: receives
 * FRAME datagrams (handed to the frame_buffer for reassembly) and sends
 * NAK datagrams back to the controller when frame_buffer_take_naks() has
 * something queued. GET /status and POST /clear stay on hw/http_server.c's
 * TCP listener - this module owns only the UDP socket, bound to the same
 * PICO_HTTP_PORT number (TCP and UDP ports are independent namespaces).
 *
 * Runs entirely from lwIP's callback context on core0 - see main.c. Frame
 * submission and NAK draining cross into the frame_buffer shared with core1
 * and with hw/http_server.c via `fb_lock` - see http_server.h for why this
 * must be the one critical_section_t main.c owns, not one created here.
 */

void udp_frame_server_init(frame_buffer_t *fb, critical_section_t *fb_lock);

/* Call from core0's loop alongside wifi_poll()/http_server_poll() - drains
 * any NAKs the frame_buffer has queued and sends them to the address the
 * most recent FRAME datagram arrived from (there's no separate "control
 * port" - see docs/docs/network-pixel-protocol.md). */
void udp_frame_server_poll(void);

/* Gates inbound frames the same way http_server.c used to gate POST
 * /frame: before the first successful SNTP sync, datagrams are still
 * received (so the last-sender address stays fresh) but discarded rather
 * than submitted, since a presentation_time_us can't be scheduled
 * correctly against an unsynced clock. */
void udp_frame_server_set_synced(bool synced);

#endif
