#include "hw/sntp_client.h"

#include <string.h>

#include "lwip/ip_addr.h"
#include "lwip/udp.h"
#include "pico/cyw43_arch.h"
#include "pico/time.h"

#include "core/sntp_offset.h"
#include "pico_config.h"

#define NTP_PORT 123
#define NTP_PACKET_LEN 48
#define NTP_UNIX_EPOCH_DIFF_S 2208988800ULL /* NTP epoch (1900) -> Unix epoch (1970) */

typedef enum { SNTP_IDLE, SNTP_WAITING_REPLY } sntp_state_t;

static struct udp_pcb *g_pcb;
static ip_addr_t g_server_addr;

static sntp_state_t g_state = SNTP_IDLE;
static bool g_burst_active = false;
static sntp_sample_t g_samples[PICO_SNTP_BURST_SAMPLES];
static int g_sample_count;
static int g_attempts;
static int64_t g_t1_us;
static absolute_time_t g_sample_deadline;

static bool g_synced = false;
static int64_t g_offset_us = 0;
static int64_t g_delay_us = 0;

static int64_t ntp_ts_to_unix_us(const uint8_t *field /* 8 bytes, big-endian NTP fixed-point */) {
    uint32_t secs = ((uint32_t)field[0] << 24) | ((uint32_t)field[1] << 16) |
                    ((uint32_t)field[2] << 8) | field[3];
    uint32_t frac = ((uint32_t)field[4] << 24) | ((uint32_t)field[5] << 16) |
                    ((uint32_t)field[6] << 8) | field[7];
    int64_t unix_s = (int64_t)secs - (int64_t)NTP_UNIX_EPOCH_DIFF_S;
    int64_t frac_us = (int64_t)(((uint64_t)frac * 1000000ULL) >> 32);
    return unix_s * 1000000 + frac_us;
}

static void recv_cb(void *arg, struct udp_pcb *pcb, struct pbuf *p, const ip_addr_t *addr, u16_t port) {
    (void)arg;
    (void)pcb;
    (void)addr;
    (void)port;

    int64_t t4_us = (int64_t)time_us_64();

    if (g_state == SNTP_WAITING_REPLY && p->tot_len >= NTP_PACKET_LEN) {
        uint8_t buf[NTP_PACKET_LEN];
        pbuf_copy_partial(p, buf, NTP_PACKET_LEN, 0);

        if (g_sample_count < PICO_SNTP_BURST_SAMPLES) {
            sntp_sample_t *s = &g_samples[g_sample_count++];
            s->t1_us = g_t1_us;
            s->t2_us = ntp_ts_to_unix_us(&buf[32]); /* Receive Timestamp */
            s->t3_us = ntp_ts_to_unix_us(&buf[40]); /* Transmit Timestamp */
            s->t4_us = t4_us;
        }
        g_state = SNTP_IDLE;
    }

    pbuf_free(p);
}

void sntp_client_init(const char *server_ip) {
    ip4addr_aton(server_ip, &g_server_addr);
    /* This "threadsafe_background" cyw43_arch variant services lwIP from a
     * low-priority IRQ context; per pico/cyw43_arch.h's own documentation,
     * any lwIP call made from outside of an lwIP-invoked callback (recv_cb
     * below is one and needs no bracketing) must be bracketed with
     * cyw43_arch_lwip_begin()/_end() or it races that background processing
     * - this is what actually caused the "tcp_receive: valid queue len"
     * PANIC in hw/http_server.c and hw/ws_frame_server.c, which had the
     * same gap. init()/send_request() here are both called from main()'s
     * loop, not from a callback, so both need it too. */
    cyw43_arch_lwip_begin();
    g_pcb = udp_new();
    udp_recv(g_pcb, recv_cb, NULL);
    cyw43_arch_lwip_end();
}

static void send_request(void) {
    cyw43_arch_lwip_begin();
    struct pbuf *p = pbuf_alloc(PBUF_TRANSPORT, NTP_PACKET_LEN, PBUF_RAM);
    if (!p) {
        cyw43_arch_lwip_end();
        return;
    }
    memset(p->payload, 0, NTP_PACKET_LEN);
    ((uint8_t *)p->payload)[0] = 0x23; /* LI=0, VN=4, Mode=3 (client) */

    g_t1_us = (int64_t)time_us_64();
    g_sample_deadline = make_timeout_time_ms(PICO_SNTP_SAMPLE_TIMEOUT_MS);
    g_state = SNTP_WAITING_REPLY;

    udp_sendto(g_pcb, p, &g_server_addr, NTP_PORT);
    pbuf_free(p);
    cyw43_arch_lwip_end();
}

void sntp_client_start_sync(void) {
    g_sample_count = 0;
    g_attempts = 1;
    g_burst_active = true;
    send_request();
}

bool sntp_client_burst_in_progress(void) {
    return g_burst_active;
}

void sntp_client_poll(void) {
    if (!g_burst_active) return;

    if (g_state == SNTP_WAITING_REPLY) {
        if (absolute_time_diff_us(get_absolute_time(), g_sample_deadline) < 0) {
            g_state = SNTP_IDLE; /* this attempt timed out; poll() below may retry */
        } else {
            return; /* still waiting on this attempt */
        }
    }

    bool have_enough = g_sample_count >= PICO_SNTP_BURST_SAMPLES;
    bool given_up = g_attempts >= PICO_SNTP_BURST_SAMPLES * 2; /* bound worst-case time if the server's unreachable */
    if (!have_enough && !given_up) {
        send_request();
        g_attempts++;
    }
    /* else: leave g_burst_active true - sntp_client_burst_done() now reports
     * true and main.c is expected to call sntp_client_finish_burst() */
}

bool sntp_client_burst_done(void) {
    if (!g_burst_active || g_state == SNTP_WAITING_REPLY) return false;
    return g_sample_count >= PICO_SNTP_BURST_SAMPLES || g_attempts >= PICO_SNTP_BURST_SAMPLES * 2;
}

void sntp_client_finish_burst(void) {
    sntp_result_t r;
    if (sntp_offset_best_of(g_samples, g_sample_count, &r)) {
        g_offset_us = r.offset_us;
        g_delay_us = r.delay_us;
        g_synced = true;
    }
    /* if no samples came back at all, g_synced (and the previous offset, if
     * any) are left as they were - a resync that fully fails shouldn't
     * un-sync a device that was already fine */
    g_burst_active = false;
}

bool sntp_client_synced(void) {
    return g_synced;
}

int64_t sntp_client_offset_us(void) {
    return g_offset_us;
}

int64_t sntp_client_last_delay_us(void) {
    return g_delay_us;
}
