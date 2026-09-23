#include "hw/ws_frame_server.h"

#include <stdio.h>
#include <string.h>

#include "lwip/tcp.h"
#include "pico/cyw43_arch.h"
#include "pico/time.h"

#include "core/http_parser.h"
#include "core/ws_handshake.h"
#include "pico_config.h"

/* Big-endian wire format - see docs/docs/network-pixel-protocol.md. */
#define TYPE_FRAME 0x01
#define TYPE_CREDIT 0x02

/* type(1) seq(4) presentation_time_us(8) */
#define FRAME_HEADER_LEN 13
#define CREDIT_MSG_LEN 5

#define WS_OPCODE_BINARY 0x2
#define WS_OPCODE_CLOSE 0x8

/* the biggest application message either side ever sends, plus the largest
 * possible WS frame header (2 + 8-byte extended length + 4-byte mask) */
#define WS_MAX_MESSAGE_LEN (FRAME_HEADER_LEN + PICO_MAX_PIXELS_TOTAL * 3)
#define WS_RECV_BUF_LEN (WS_MAX_MESSAGE_LEN + 14)

typedef struct {
    struct tcp_pcb *pcb;
    bool in_use;
    bool handshake_done;
    http_parser_t handshake_parser;

    uint8_t buf[WS_RECV_BUF_LEN];
    size_t  buf_len;
} ws_conn_t;

static ws_conn_t g_conn;
static frame_buffer_t *g_fb;
static critical_section_t *g_fb_lock;
static volatile bool g_synced = false;

static uint32_t g_last_sent_free_slots;
static absolute_time_t g_next_heartbeat;

/* FRAME messages that arrive before the first SNTP sync completes - counted
 * and logged (throttled) here since ws_frame_server_set_synced() decides
 * whether to drop them entirely silently otherwise, which made "controller
 * connected and streaming, still no LEDs" indistinguishable from "nothing is
 * arriving at all" - see docs/docs/time-sync.md and pico_config.h's
 * CONTROLLER_TIME_SERVER_IP. */
static uint32_t g_frames_dropped_presync;

static uint32_t read_u32(const uint8_t *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) | ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

static int64_t read_i64(const uint8_t *p) {
    uint64_t v = 0;
    for (int i = 0; i < 8; i++) v = (v << 8) | p[i];
    return (int64_t)v;
}

static void write_u32(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)(v >> 24);
    p[1] = (uint8_t)(v >> 16);
    p[2] = (uint8_t)(v >> 8);
    p[3] = (uint8_t)v;
}

/* Server->client frames are never masked and, for our two message types,
 * never need the 16-bit length variant's big sibling (64-bit) - CREDIT is 5
 * bytes and FRAME is never sent this direction. */
static void send_ws_binary(struct tcp_pcb *pcb, const uint8_t *payload, size_t len) {
    uint8_t header[4];
    size_t header_len;
    header[0] = 0x80 | WS_OPCODE_BINARY;
    if (len <= 125) {
        header[1] = (uint8_t)len;
        header_len = 2;
    } else {
        header[1] = 126;
        header[2] = (uint8_t)(len >> 8);
        header[3] = (uint8_t)len;
        header_len = 4;
    }
    if (tcp_write(pcb, header, (u16_t)header_len, TCP_WRITE_FLAG_COPY | TCP_WRITE_FLAG_MORE) != ERR_OK) return;
    if (len > 0) tcp_write(pcb, payload, (u16_t)len, TCP_WRITE_FLAG_COPY);
    tcp_output(pcb);
}

static void send_credit(uint32_t free_slots) {
    if (!g_conn.in_use || !g_conn.handshake_done) return;
    uint8_t msg[CREDIT_MSG_LEN];
    msg[0] = TYPE_CREDIT;
    write_u32(&msg[1], free_slots);
    send_ws_binary(g_conn.pcb, msg, sizeof(msg));
    g_last_sent_free_slots = free_slots;
    g_next_heartbeat = make_timeout_time_ms(PICO_WS_CREDIT_HEARTBEAT_MS);
}

static void handle_frame_message(const uint8_t *payload, size_t len) {
    if (len < FRAME_HEADER_LEN) return;
    if (!g_synced) {
        /* mirrors the old UDP path's pre-sync discard - logged on the first
         * occurrence and every 100th after, so a controller stuck sending
         * into an unsynced device is visible instead of just "no LEDs" */
        g_frames_dropped_presync++;
        if (g_frames_dropped_presync == 1 || g_frames_dropped_presync % 100 == 0) {
            printf("ws: dropping frame - not time-synced yet (%lu dropped so far)\n",
                   (unsigned long)g_frames_dropped_presync);
        }
        return;
    }

    uint32_t seq = read_u32(&payload[1]);
    int64_t t_us = read_i64(&payload[5]);
    const uint8_t *pixels = payload + FRAME_HEADER_LEN;
    uint16_t pixels_len = (uint16_t)(len - FRAME_HEADER_LEN);

    critical_section_enter_blocking(g_fb_lock);
    frame_buffer_submit_frame(g_fb, t_us, seq, pixels, pixels_len);
    uint32_t free_slots = frame_buffer_free_slots(g_fb);
    critical_section_exit(g_fb_lock);

    if (free_slots != g_last_sent_free_slots) send_credit(free_slots);
}

typedef enum { WS_FRAME_NEED_MORE, WS_FRAME_GOT, WS_FRAME_ERROR } ws_frame_result_t;

/* Parses one WS frame out of c->buf if a complete one is available,
 * dispatches it, and compacts the buffer. No fragmentation support - the
 * controller always sends single, unfragmented frames - and a client frame
 * arriving unmasked is a protocol violation (masked=false is only ever
 * valid server->client, which is the direction we send, not receive). */
static ws_frame_result_t process_one_ws_frame(ws_conn_t *c) {
    if (c->buf_len < 2) return WS_FRAME_NEED_MORE;

    uint8_t b0 = c->buf[0], b1 = c->buf[1];
    uint8_t opcode = b0 & 0x0F;
    bool masked = (b1 & 0x80) != 0;
    uint64_t len = b1 & 0x7F;
    size_t pos = 2;

    if (len == 126) {
        if (c->buf_len < 4) return WS_FRAME_NEED_MORE;
        len = ((uint64_t)c->buf[2] << 8) | c->buf[3];
        pos = 4;
    } else if (len == 127) {
        if (c->buf_len < 10) return WS_FRAME_NEED_MORE;
        len = 0;
        for (int i = 0; i < 8; i++) len = (len << 8) | c->buf[2 + i];
        pos = 10;
    }

    if (!masked) return WS_FRAME_ERROR;
    if (pos + 4 > sizeof(c->buf) || pos + 4 + len > sizeof(c->buf)) return WS_FRAME_ERROR; /* bigger than any message we expect */
    if (c->buf_len < pos + 4) return WS_FRAME_NEED_MORE;

    const uint8_t mask_key[4] = {c->buf[pos], c->buf[pos + 1], c->buf[pos + 2], c->buf[pos + 3]};
    pos += 4;
    if (c->buf_len < pos + len) return WS_FRAME_NEED_MORE;

    uint8_t *payload = &c->buf[pos];
    for (uint64_t i = 0; i < len; i++) payload[i] ^= mask_key[i % 4];

    if (opcode == WS_OPCODE_CLOSE) return WS_FRAME_ERROR; /* caller closes the connection */
    if (opcode == WS_OPCODE_BINARY && len >= 1 && payload[0] == TYPE_FRAME) {
        handle_frame_message(payload, (size_t)len);
    }
    /* anything else (ping/pong, an unrecognised type byte) is ignored - neither side ever sends them */

    size_t frame_len = pos + len;
    memmove(c->buf, c->buf + frame_len, c->buf_len - frame_len);
    c->buf_len -= frame_len;
    return WS_FRAME_GOT;
}

/* tcp_close() can fail (return non-ERR_OK, e.g. ERR_MEM) if it can't
 * complete synchronously - in that case the pcb is NOT freed, stays
 * registered, and keeps calling back into whatever tcp_arg() last pointed
 * it at. close_conn() used to memset(c, ...) unconditionally right after
 * tcp_close(), so a pcb that lingered this way kept firing recv_cb/err_cb
 * with `arg` pointing at a struct we'd already zeroed and handed to the
 * *next* accepted connection - two unrelated TCP connections then shared
 * one ws_conn_t, corrupting each other's buffer/state. That's what surfaced
 * as lwIP's "tcp_receive: valid queue length" PANIC. Detaching every
 * callback *before* tcp_close() guarantees this pcb can never call back
 * into our code again, however long it takes to actually finish closing. */
static void close_conn(ws_conn_t *c) {
    if (c->pcb) {
        tcp_arg(c->pcb, NULL);
        tcp_recv(c->pcb, NULL);
        tcp_err(c->pcb, NULL);
        tcp_close(c->pcb);
    }
    memset(c, 0, sizeof(*c));
}

static err_t recv_cb(void *arg, struct tcp_pcb *tpcb, struct pbuf *p, err_t err) {
    ws_conn_t *c = (ws_conn_t *)arg;
    (void)err;

    /* Shouldn't happen now that close_conn() detaches tcp_arg() before
     * tcp_close() - kept as cheap insurance against ever repeating the
     * stale-callback class of bug this file just got bitten by. */
    if (!c) {
        if (p) pbuf_free(p);
        return ERR_OK;
    }

    if (!p) {
        printf("ws: connection closed by peer\n");
        close_conn(c);
        return ERR_OK;
    }

    /* Once close_conn() below calls tcp_close(c->pcb), the pcb may be freed
     * and its memory reused for a different connection before this function
     * returns - calling tcp_recved(tpcb, ...) on it afterwards (as the
     * `done:` label used to do unconditionally) corrupts whichever
     * unrelated connection got that memory next. That's what caused the
     * "PANIC: unsent_oversize mismatch" crash: under a burst of frames this
     * path closes connections often, and each stray post-close tcp_recved()
     * silently corrupted the next accepted pcb until one eventually
     * asserted. Track whether we closed it and skip that call if so. */
    bool closed = false;

    struct pbuf *cur = p;
    while (cur) {
        const uint8_t *data = (const uint8_t *)cur->payload;
        size_t avail = cur->len;

        if (!c->handshake_done) {
            while (avail > 0) {
                size_t consumed = 0;
                http_parse_result_t r = http_parser_feed(&c->handshake_parser, data, avail, &consumed);
                data += consumed;
                avail -= consumed;

                if (r == HTTP_PARSE_ERROR) {
                    printf("ws: malformed handshake, closing\n");
                    close_conn(c);
                    closed = true;
                    goto done;
                }
                if (r == HTTP_PARSE_HEADERS_DONE) {
                    const http_request_t *req = http_parser_request(&c->handshake_parser);
                    if (req->method != HTTP_METHOD_GET || !req->have_ws_key) {
                        printf("ws: not a websocket upgrade request, closing\n");
                        close_conn(c);
                        closed = true;
                        goto done;
                    }

                    char accept[29];
                    ws_compute_accept_key(req->ws_key, accept);
                    char resp[192];
                    int n = snprintf(resp, sizeof(resp),
                        "HTTP/1.1 101 Switching Protocols\r\n"
                        "Upgrade: websocket\r\n"
                        "Connection: Upgrade\r\n"
                        "Sec-WebSocket-Accept: %s\r\n\r\n", accept);
                    if (n < 0 || (size_t)n >= sizeof(resp)) {
                        close_conn(c);
                        closed = true;
                        goto done;
                    }
                    tcp_write(tpcb, resp, (u16_t)n, TCP_WRITE_FLAG_COPY);
                    tcp_output(tpcb);
                    c->handshake_done = true;
                    printf("ws: handshake complete\n");

                    critical_section_enter_blocking(g_fb_lock);
                    uint32_t free_slots = frame_buffer_free_slots(g_fb);
                    critical_section_exit(g_fb_lock);
                    send_credit(free_slots);
                    break; /* any remaining `avail` bytes are WS frame bytes, handled below */
                }
            }
        }

        /* Drain incrementally rather than requiring this whole chunk to fit
         * before processing anything: the controller legitimately bursts
         * many frames back-to-back once it has credit (its own PREROLL+
         * BUFFER lookahead queue draining all at once), and lwIP is free to
         * coalesce several of those into one incoming chunk bigger than one
         * message. Fill up to whatever room is currently free, drain every
         * complete frame that unblocks, and repeat - only a single frame
         * that alone can't fit even in an empty buffer is a real error. */
        while (c->handshake_done && avail > 0) {
            size_t room = sizeof(c->buf) - c->buf_len;
            if (room == 0) {
                printf("ws: message too large, closing\n");
                close_conn(c);
                closed = true;
                goto done;
            }
            size_t take = avail < room ? avail : room;
            memcpy(c->buf + c->buf_len, data, take);
            c->buf_len += take;
            data += take;
            avail -= take;

            ws_frame_result_t r;
            while ((r = process_one_ws_frame(c)) == WS_FRAME_GOT) { }
            if (r == WS_FRAME_ERROR) {
                close_conn(c);
                closed = true;
                goto done;
            }
        }

        cur = cur->next;
    }

done:
    if (!closed) tcp_recved(tpcb, p->tot_len);
    pbuf_free(p);
    return ERR_OK;
}

static void err_cb(void *arg, err_t err) {
    (void)err;
    ws_conn_t *c = (ws_conn_t *)arg;
    if (c) memset(c, 0, sizeof(*c)); /* lwIP has already freed the pcb by the time this fires - don't tcp_close() it */
}

static err_t accept_cb(void *arg, struct tcp_pcb *newpcb, err_t err) {
    (void)arg;
    (void)err;

    if (g_conn.in_use) {
        printf("ws: new connection from %s:%u replaces the current one\n",
               ipaddr_ntoa(&newpcb->remote_ip), newpcb->remote_port);
        close_conn(&g_conn);
    }

    printf("ws: connection from %s:%u\n", ipaddr_ntoa(&newpcb->remote_ip), newpcb->remote_port);
    g_conn.pcb = newpcb;
    g_conn.in_use = true;
    http_parser_reset(&g_conn.handshake_parser);
    tcp_arg(newpcb, &g_conn);
    tcp_recv(newpcb, recv_cb);
    tcp_err(newpcb, err_cb);
    return ERR_OK;
}

void ws_frame_server_init(frame_buffer_t *fb, critical_section_t *fb_lock) {
    g_fb = fb;
    g_fb_lock = fb_lock;
    memset(&g_conn, 0, sizeof(g_conn));

    /* This "threadsafe_background" cyw43_arch variant services lwIP from a
     * low-priority IRQ context; per pico/cyw43_arch.h's own documentation,
     * ANY lwIP call made from outside of an lwIP-invoked callback (accept_cb/
     * recv_cb/err_cb below all qualify and need no bracketing - init() and
     * poll() below are the two places that don't) must be bracketed with
     * cyw43_arch_lwip_begin()/_end() or it races that background processing.
     * This file (and http_server.c) missed that entirely, which is what
     * actually caused the "tcp_receive: valid queue len" PANIC - not the
     * pcb-lifecycle bug fixed earlier, which was real but a different issue. */
    cyw43_arch_lwip_begin();
    struct tcp_pcb *pcb = tcp_new();
    tcp_bind(pcb, IP_ADDR_ANY, PICO_WS_PORT);
    pcb = tcp_listen_with_backlog(pcb, 1);
    tcp_accept(pcb, accept_cb);
    cyw43_arch_lwip_end();

    g_next_heartbeat = make_timeout_time_ms(PICO_WS_CREDIT_HEARTBEAT_MS);
}

void ws_frame_server_poll(void) {
    if (!g_conn.in_use || !g_conn.handshake_done) return;

    critical_section_enter_blocking(g_fb_lock);
    uint32_t free_slots = frame_buffer_free_slots(g_fb);
    critical_section_exit(g_fb_lock);

    if (free_slots != g_last_sent_free_slots || absolute_time_diff_us(get_absolute_time(), g_next_heartbeat) <= 0) {
        /* send_credit() -> tcp_write()/tcp_output() - called from core0's
         * plain main loop, not from an lwIP callback, so it must be
         * bracketed (see ws_frame_server_init()'s comment above). */
        cyw43_arch_lwip_begin();
        send_credit(free_slots);
        cyw43_arch_lwip_end();
    }
}

void ws_frame_server_set_synced(bool synced) {
    g_synced = synced;
}

uint32_t ws_frame_server_frames_dropped_presync(void) {
    return g_frames_dropped_presync;
}
