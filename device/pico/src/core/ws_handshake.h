#ifndef CORE_WS_HANDSHAKE_H
#define CORE_WS_HANDSHAKE_H

/* Computes a WebSocket handshake's Sec-WebSocket-Accept value (RFC 6455
 * section 1.3): base64(sha1(client_key + the RFC's fixed GUID)). Used by
 * hw/ws_frame_server.c to answer the controller's upgrade request. No Pico
 * SDK dependency - host-tested (test/test_ws_handshake.c) against the RFC's
 * own worked example, since a hand-rolled SHA-1 is easy to get subtly
 * wrong. */
void ws_compute_accept_key(const char *client_key, char accept_out[29]);

#endif
