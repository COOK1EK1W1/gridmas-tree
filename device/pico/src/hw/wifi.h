#ifndef HW_WIFI_H
#define HW_WIFI_H

#include <stdbool.h>
#include <stdint.h>

/* Brings up Wi-Fi (cyw43/lwIP), disables power-save, and joins the hardcoded
 * network from wifi_secrets.h. Blocks (retrying indefinitely) until the
 * first successful association + DHCP lease.
 *
 * After that, call wifi_poll() regularly from core0's main loop - it
 * re-drives lwIP's background work and, per docs/docs/pico-device.md's
 * "previously connected" policy, forces a full device reboot via the
 * watchdog if the link has been down for too long SINCE this device's first
 * successful connect this boot. A device that has never yet connected just
 * keeps retrying quietly instead - this avoids boot-looping a Pico with no
 * Wi-Fi in range, e.g. on a bench during development.
 */
void wifi_init_and_connect_blocking(void);
void wifi_poll(void);
bool wifi_is_up(void);

/* Current signal strength (dBm, negative - closer to 0 is stronger) to the
 * associated AP, or 0 if not connected. A weak/marginal RSSI is a common
 * cause of intermittent connect timeouts on the CYW43439's small onboard
 * antenna that has nothing to do with this firmware's protocol logic -
 * surfaced in main.c's periodic diagnostic line for that reason. */
int32_t wifi_rssi(void);

#endif
