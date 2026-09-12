#include "hw/udp_frame_server.h"

#include <string.h>

#include "lwip/udp.h"
#include "pico/critical_section.h"

#include "pico_config.h"

/* Big-endian wire format - see docs/docs/network-pixel-protocol.md. */
#define TYPE_FRAME 0x01
#define TYPE_NAK 0x02

/* type(1) seq(4) presentation_time_us(8) chunk_index(1) chunk_count(1) */
#define FRAME_HEADER_LEN 15
/* type(1) seq(4) chunk_index(1) */
#define NAK_LEN 6

static struct udp_pcb *g_pcb;
static frame_buffer_t *g_fb;
static critical_section_t *g_fb_lock; /* owned by main.c - shared with core1 and http_server.c */

static volatile bool g_synced = false;

/* Who to send NAKs to - the address the most recent FRAME datagram arrived
 * from. Both core0 execution contexts (the lwIP callback that writes this,
 * and main.c's loop - via udp_frame_server_poll() - that reads it) run on
 * the same core with cyw43's "threadsafe background" driver, so this is
 * never truly concurrent, but volatile (matching g_synced et al. in
 * http_server.c) keeps the compiler from caching a stale value across that
 * callback/loop boundary. */
static volatile ip_addr_t g_last_sender_ip;
static volatile u16_t g_last_sender_port;
static volatile bool g_have_last_sender = false;

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

static void recv_cb(void *arg, struct udp_pcb *pcb, struct pbuf *p, const ip_addr_t *addr, u16_t port) {
    (void)arg;
    (void)pcb;

    if (p->tot_len < FRAME_HEADER_LEN) {
        pbuf_free(p);
        return;
    }

    uint8_t header[FRAME_HEADER_LEN];
    pbuf_copy_partial(p, header, FRAME_HEADER_LEN, 0);

    g_last_sender_ip = *addr;
    g_last_sender_port = port;
    g_have_last_sender = true;

    if (header[0] != TYPE_FRAME) {
        pbuf_free(p);
        return;
    }

    uint32_t seq = read_u32(&header[1]);
    int64_t presentation_time_us = read_i64(&header[5]);
    uint8_t chunk_index = header[13];
    uint8_t chunk_count = header[14];
    uint16_t payload_len = (uint16_t)(p->tot_len - FRAME_HEADER_LEN);

    /* Before time-sync, presentation_time_us can't be scheduled against a
     * meaningful "now" - discard rather than submit (mirrors
     * http_server.c's old pre-sync 503 rejection), but the last-sender
     * address above is still recorded either way. */
    if (g_synced && payload_len > 0 && payload_len <= PICO_PIXELS_PER_CHUNK * 3) {
        /* static, not stack: this callback runs single-threaded (NO_SYS=1),
         * so one scratch buffer is safe and avoids putting up to 1440B on
         * the lwIP callback's stack per datagram. */
        static uint8_t payload_buf[PICO_PIXELS_PER_CHUNK * 3];
        pbuf_copy_partial(p, payload_buf, payload_len, FRAME_HEADER_LEN);

        critical_section_enter_blocking(g_fb_lock);
        frame_buffer_submit_chunk(g_fb, presentation_time_us, seq, chunk_index, chunk_count,
                                   payload_buf, payload_len);
        critical_section_exit(g_fb_lock);
    }

    pbuf_free(p);
}

void udp_frame_server_init(frame_buffer_t *fb, critical_section_t *fb_lock) {
    g_fb = fb;
    g_fb_lock = fb_lock;

    g_pcb = udp_new();
    udp_bind(g_pcb, IP_ADDR_ANY, PICO_HTTP_PORT);
    udp_recv(g_pcb, recv_cb, NULL);
}

void udp_frame_server_poll(void) {
    if (!g_have_last_sender) return; /* nowhere to send a NAK yet */

    /* Snapshot into plain (non-volatile) locals: gives every NAK sent by
     * this call the same destination even if recv_cb() updates the address
     * partway through, and sidesteps passing a volatile-qualified pointer
     * to udp_sendto()'s plain `const ip_addr_t *` parameter. */
    ip_addr_t dest_ip = g_last_sender_ip;
    u16_t dest_port = g_last_sender_port;

    uint32_t naks_seq[PICO_NAK_QUEUE_CAPACITY];
    uint8_t naks_chunk[PICO_NAK_QUEUE_CAPACITY];
    uint8_t n;

    critical_section_enter_blocking(g_fb_lock);
    n = frame_buffer_take_naks(g_fb, naks_seq, naks_chunk, PICO_NAK_QUEUE_CAPACITY);
    critical_section_exit(g_fb_lock);

    for (uint8_t i = 0; i < n; i++) {
        struct pbuf *out = pbuf_alloc(PBUF_TRANSPORT, NAK_LEN, PBUF_RAM);
        if (!out) continue; /* out of pbufs - this NAK is lost, same as any other loss */

        uint8_t *d = (uint8_t *)out->payload;
        d[0] = TYPE_NAK;
        write_u32(&d[1], naks_seq[i]);
        d[5] = naks_chunk[i];

        udp_sendto(g_pcb, out, &dest_ip, dest_port);
        pbuf_free(out);
    }
}

void udp_frame_server_set_synced(bool synced) {
    g_synced = synced;
}
