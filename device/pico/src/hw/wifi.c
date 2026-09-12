#include "hw/wifi.h"

#include <stdio.h>

#include "hardware/watchdog.h"
#include "lwip/netif.h"
#include "pico/cyw43_arch.h"

#include "pico_config.h"
#include "wifi_secrets.h"

/* Each connect attempt is one blocking SDK call we can't feed the watchdog
 * during - must stay safely under PICO_WATCHDOG_TIMEOUT_MS (pico_config.h),
 * which is sized specifically to leave room for this. */
#define WIFI_CONNECT_ATTEMPT_TIMEOUT_MS 6000

static bool ever_connected = false;
static bool link_was_up = false;
static absolute_time_t down_since;

void wifi_init_and_connect_blocking(void) {
    if (cyw43_arch_init()) {
        /* nothing useful to do without the Wi-Fi chip - spin (fed by the
         * general watchdog, already armed by main.c before this function was
         * called, so this reboots and retries cyw43_arch_init() from
         * scratch rather than hanging forever on a possibly-transient
         * failure) */
        while (true) {
            tight_loop_contents();
        }
    }

    cyw43_arch_enable_sta_mode();

    /* Wi-Fi power-save costs exactly the kind of inbound-packet latency that
     * turned out to be the dominant bottleneck when this project first
     * diagnosed the real device's frame throughput - see
     * docs/docs/network-pixel-protocol.md's "Device performance notes".
     * Disable it outright rather than relearn that lesson here. */
    cyw43_wifi_pm(&cyw43_state, CYW43_NO_POWERSAVE_MODE);

    printf("wifi: connecting to \"%s\"...\n", WIFI_SSID);
    while (cyw43_arch_wifi_connect_timeout_ms(WIFI_SSID, WIFI_PASSWORD, CYW43_AUTH_WPA2_AES_PSK,
                                               WIFI_CONNECT_ATTEMPT_TIMEOUT_MS) != 0) {
        printf("wifi: connect failed, retrying\n");
        /* each attempt is individually bounded (WIFI_CONNECT_ATTEMPT_TIMEOUT_MS),
         * but retrying indefinitely here - by design, see
         * docs/docs/pico-device.md's "never yet connected" policy - must not
         * itself starve the general watchdog armed by main.c before this
         * function was called */
        watchdog_update();
    }

    ever_connected = true;
    link_was_up = true;

    /* the IP DHCP handed us - this is what CONTROLLER_TIME_SERVER_IP's
     * counterpart, GRIDMAS_DEVICE_ADDRESS on the controller, needs to point
     * at for this device (see docs/docs/pico-device.md's DHCP+reservation
     * addressing) */
    printf("wifi: connected, IP address %s\n", ip4addr_ntoa(netif_ip4_addr(netif_default)));
}

void wifi_poll(void) {
    cyw43_arch_poll();

    bool up = wifi_is_up();

    if (!ever_connected) return; /* haven't connected yet this boot - keep retrying quietly, no forced reboot */

    if (up) {
        link_was_up = true;
        return;
    }

    if (link_was_up) {
        /* link just dropped - start the clock */
        link_was_up = false;
        down_since = get_absolute_time();
        printf("wifi: link down - will reboot if not restored within %ds\n", PICO_WIFI_LOSS_REBOOT_TIMEOUT_MS / 1000);
        return;
    }

    if (absolute_time_diff_us(down_since, get_absolute_time()) > PICO_WIFI_LOSS_REBOOT_TIMEOUT_MS * 1000) {
        printf("wifi: down for too long after a previous connection - rebooting\n");
        watchdog_reboot(0, 0, 0);
        while (true) {
            tight_loop_contents();
        }
    }
}

bool wifi_is_up(void) {
    return cyw43_tcpip_link_status(&cyw43_state, CYW43_ITF_STA) == CYW43_LINK_UP;
}
