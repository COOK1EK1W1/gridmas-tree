#include "hw/http_server.h"

#include <stdio.h>
#include <string.h>

#include "lwip/tcp.h"
#include "pico/critical_section.h"
#include "pico/time.h"

#include "core/http_parser.h"
#include "hw/status_json.h"
#include "pico_config.h"

typedef struct {
    struct tcp_pcb *pcb;
    http_parser_t parser;
    bool in_use;

    char resp_buf[512];
} http_conn_t;

static http_conn_t conns[PICO_MAX_CONCURRENT_CONNS];
static frame_buffer_t *g_fb;
static critical_section_t *g_fb_lock; /* owned by main.c - shared with core1 and udp_frame_server.c */

static volatile bool g_synced = false;
static volatile int64_t g_sync_offset_us = 0;
static volatile int64_t g_sync_delay_us = 0;
static absolute_time_t g_boot_time;

static http_conn_t *conn_alloc(void) {
    for (int i = 0; i < PICO_MAX_CONCURRENT_CONNS; i++) {
        if (!conns[i].in_use) {
            memset(&conns[i], 0, sizeof(conns[i]));
            conns[i].in_use = true;
            return &conns[i];
        }
    }
    return NULL;
}

static err_t send_response(http_conn_t *c, int status, const char *status_text,
                            const char *body, size_t body_len, const char *content_type) {
    int n = snprintf(c->resp_buf, sizeof(c->resp_buf),
        "HTTP/1.1 %d %s\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %u\r\n"
        "Connection: keep-alive\r\n"
        "\r\n",
        status, status_text, content_type ? content_type : "text/plain", (unsigned)body_len);
    if (n < 0 || (size_t)n >= sizeof(c->resp_buf)) return ERR_BUF;

    err_t err = tcp_write(c->pcb, c->resp_buf, (u16_t)n, TCP_WRITE_FLAG_COPY | TCP_WRITE_FLAG_MORE);
    if (err != ERR_OK) return err;
    if (body_len > 0) {
        err = tcp_write(c->pcb, body, (u16_t)body_len, TCP_WRITE_FLAG_COPY);
        if (err != ERR_OK) return err;
    }
    return tcp_output(c->pcb);
}

static err_t respond_simple(http_conn_t *c, int status, const char *status_text) {
    return send_response(c, status, status_text, NULL, 0, NULL);
}

static err_t handle_status(http_conn_t *c) {
    char body[400];
    int64_t now_us = (int64_t)time_us_64() + (g_synced ? g_sync_offset_us : 0);
    uint32_t uptime_s = (uint32_t)(absolute_time_diff_us(g_boot_time, get_absolute_time()) / 1000000);
    size_t len = status_json_build(body, sizeof(body), g_fb, g_synced, g_sync_offset_us, g_sync_delay_us,
                                    uptime_s, now_us);
    return send_response(c, 200, "OK", body, len, "application/json");
}

static err_t handle_clear(http_conn_t *c) {
    critical_section_enter_blocking(g_fb_lock);
    frame_buffer_init(g_fb); /* drops every buffered/pending frame */
    critical_section_exit(g_fb_lock);
    return respond_simple(c, 200, "OK");
    /* blanking the strip itself is main.c's job via the ws2812_output_blank()
     * call this triggers indirectly - see docs/docs/pico-device.md's Q18 for
     * why blanking only happens on boot, not on every /clear or empty buffer */
}

static err_t recv_cb(void *arg, struct tcp_pcb *tpcb, struct pbuf *p, err_t err) {
    http_conn_t *c = (http_conn_t *)arg;
    (void)err;

    if (!p) { /* remote closed */
        tcp_close(tpcb);
        c->in_use = false;
        return ERR_OK;
    }

    struct pbuf *cur = p;

    while (cur) {
        const uint8_t *data = (const uint8_t *)cur->payload;
        size_t avail = cur->len;

        while (avail > 0) {
            size_t consumed = 0;
            http_parse_result_t r = http_parser_feed(&c->parser, data, avail, &consumed);
            data += consumed;
            avail -= consumed;

            if (r == HTTP_PARSE_ERROR) {
                printf("http: malformed request, closing connection - 400\n");
                respond_simple(c, 400, "bad request");
                tcp_close(tpcb);
                c->in_use = false;
                goto done;
            }
            if (r == HTTP_PARSE_HEADERS_DONE) {
                const http_request_t *req = http_parser_request(&c->parser);
                err_t werr;

                if (req->method == HTTP_METHOD_GET && strcmp(req->path, "/status") == 0) {
                    werr = handle_status(c);
                } else if (req->method == HTTP_METHOD_POST && strcmp(req->path, "/clear") == 0) {
                    werr = handle_clear(c);
                } else {
                    printf("http: unknown route %s - 404\n", req->path);
                    werr = respond_simple(c, 404, "not found");
                }
                http_parser_reset(&c->parser);

                if (werr != ERR_OK) {
                    tcp_close(tpcb);
                    c->in_use = false;
                    goto done;
                }
            }
            /* HTTP_PARSE_NEED_MORE: consumed everything available this pass */
        }

        cur = cur->next;
    }

done:
    tcp_recved(tpcb, p->tot_len);
    pbuf_free(p);
    return ERR_OK;
}

static void err_cb(void *arg, err_t err) {
    (void)err;
    http_conn_t *c = (http_conn_t *)arg;
    if (c) c->in_use = false;
}

static err_t accept_cb(void *arg, struct tcp_pcb *newpcb, err_t err) {
    (void)arg;
    (void)err;

    http_conn_t *c = conn_alloc();
    if (!c) {
        /* connection cap reached (PICO_MAX_CONCURRENT_CONNS) - refuse
         * cleanly. /status and /clear are the only routes left on this
         * listener, so this should be rare; if it shows up often, raise
         * PICO_MAX_CONCURRENT_CONNS. */
        printf("http: refusing connection from %s:%u - at PICO_MAX_CONCURRENT_CONNS (%d)\n",
               ipaddr_ntoa(&newpcb->remote_ip), newpcb->remote_port, PICO_MAX_CONCURRENT_CONNS);
        tcp_close(newpcb);
        return ERR_OK;
    }

    printf("http: connection from %s:%u\n", ipaddr_ntoa(&newpcb->remote_ip), newpcb->remote_port);
    c->pcb = newpcb;
    http_parser_reset(&c->parser);
    tcp_arg(newpcb, c);
    tcp_recv(newpcb, recv_cb);
    tcp_err(newpcb, err_cb);
    return ERR_OK;
}

void http_server_init(frame_buffer_t *fb, critical_section_t *fb_lock) {
    g_fb = fb;
    g_fb_lock = fb_lock;
    g_boot_time = get_absolute_time();

    struct tcp_pcb *pcb = tcp_new();
    tcp_bind(pcb, IP_ADDR_ANY, PICO_HTTP_PORT);
    pcb = tcp_listen_with_backlog(pcb, PICO_MAX_CONCURRENT_CONNS);
    tcp_accept(pcb, accept_cb);
}

void http_server_poll(void) {
    /* nothing needed today - see the header comment */
}

void http_server_set_synced(bool synced, int64_t offset_us, int64_t delay_us) {
    g_synced = synced;
    g_sync_offset_us = offset_us;
    g_sync_delay_us = delay_us;
}
