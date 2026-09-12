#ifndef LWIPOPTS_H
#define LWIPOPTS_H

/* lwIP configuration for this device - required by pico_cyw43_arch_lwip_*
 * (lwIP itself ships no default). NO_SYS=1 + the raw API only (no lwIP
 * sockets/netconn layer - hw/http_server.c and hw/sntp_client.c talk to
 * tcp_pcb/udp_pcb directly), matching the "no RTOS, callback-driven"
 * architecture in docs/docs/pico-device.md.
 *
 * Derived from the standard lwipopts.h template used across the
 * pico-examples Pico W Wi-Fi examples, trimmed to what this device uses. */

#define NO_SYS                      1
#define LWIP_SOCKET                 0
#define LWIP_NETCONN                0

#define MEM_ALIGNMENT               4
#define MEM_SIZE                    (16 * 1024)

/* a couple of headroom slots above PICO_MAX_CONCURRENT_CONNS (see
 * pico_config.h) for the listening pcb and any pcb briefly in TIME_WAIT */
#define MEMP_NUM_TCP_PCB            6
#define MEMP_NUM_TCP_PCB_LISTEN     1
#define MEMP_NUM_TCP_SEG            32
/* one headroom slot above the two in active use (hw/sntp_client.c,
 * hw/udp_frame_server.c) */
#define MEMP_NUM_UDP_PCB            3
#define MEMP_NUM_PBUF               24
#define PBUF_POOL_SIZE              24

#define LWIP_ARP                    1
#define LWIP_ETHERNET               1
#define LWIP_ICMP                   1
#define LWIP_RAW                    0

#define TCP_MSS                     1460
#define TCP_WND                     (8 * TCP_MSS)
#define TCP_SND_BUF                 (8 * TCP_MSS)
#define TCP_SND_QUEUELEN            ((4 * (TCP_SND_BUF) + (TCP_MSS - 1)) / (TCP_MSS))

#define LWIP_NETIF_STATUS_CALLBACK  1
#define LWIP_NETIF_LINK_CALLBACK    1
#define LWIP_NETIF_HOSTNAME         1

#define LWIP_DHCP                   1
#define LWIP_DNS                    0

#define LWIP_TCP                    1
#define LWIP_UDP                    1

#define LWIP_STATS                  0
#define LINK_STATS                  0

#define CHECKSUM_GEN_IP             1
#define CHECKSUM_GEN_UDP            1
#define CHECKSUM_GEN_TCP            1
#define CHECKSUM_CHECK_IP           1
#define CHECKSUM_CHECK_UDP          1
#define CHECKSUM_CHECK_TCP          1
#define LWIP_CHECKSUM_ON_COPY       1

#define LWIP_DEBUG                  0

#endif
