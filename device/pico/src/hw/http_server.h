#ifndef HW_HTTP_SERVER_H
#define HW_HTTP_SERVER_H

#include <stdbool.h>
#include <stdint.h>

#include "pico/critical_section.h"

#include "core/frame_buffer.h"

/* Hand-rolled HTTP/1.1 server on lwIP's raw tcp_pcb API, implementing
 * docs/docs/network-pixel-protocol.md's control plane: GET /status and
 * POST /clear. Frame data (and NAK-based retransmission) is UDP, not
 * HTTP - see hw/udp_frame_server.c. Supports keep-alive (see
 * docs/docs/pico-device.md's Q4) - a connection stays open across
 * multiple requests instead of forcing a handshake per request.
 *
 * Runs entirely from lwIP's callback context on core0 - see main.c.
 * /clear crosses into the frame_buffer shared with core1 (and with
 * hw/udp_frame_server.c's access from the same lwIP callback context) via
 * `fb_lock`, since frame_buffer.c is not thread-safe on its own. main.c
 * owns the one critical_section_t and passes the same pointer to
 * http_server_init(), udp_frame_server_init(), and core1's own frame_buffer
 * calls - each module creating its own critical_section_t here would claim
 * separate hardware spinlocks that don't exclude each other at all. */

void http_server_init(frame_buffer_t *fb, critical_section_t *fb_lock);

/* Call from core0's loop alongside wifi_poll()/sntp_client_poll() - kept as
 * a hook for future lwIP-driven housekeeping (e.g. stale-connection GC);
 * nothing needed here today since lwIP's own background processing is
 * driven from cyw43_arch_poll() in wifi.c. */
void http_server_poll(void);

/* Feeds GET /status's reported sync state. */
void http_server_set_synced(bool synced, int64_t offset_us, int64_t delay_us);

#endif
