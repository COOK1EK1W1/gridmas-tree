#ifndef HW_STATUS_JSON_H
#define HW_STATUS_JSON_H

#include <stddef.h>
#include <stdint.h>

#include "core/frame_buffer.h"

/* Builds the GET /status JSON body (see docs/docs/network-pixel-protocol.md
 * and docs/docs/pico-device.md for this device type's field semantics -
 * device_name is this board's unique factory ID, pixel_count is a capacity
 * ceiling rather than a configured count). Returns the number of bytes
 * written (excluding the NUL terminator), or 0 if buf_len was too small. */
size_t status_json_build(char *buf, size_t buf_len, const frame_buffer_t *fb,
                          bool synced, int64_t last_sync_offset_us, int64_t last_sync_delay_us,
                          uint32_t uptime_s, int64_t now_us);

#endif
