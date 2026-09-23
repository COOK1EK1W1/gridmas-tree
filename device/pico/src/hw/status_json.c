#include "hw/status_json.h"

#include <stdio.h>

#include "pico/unique_id.h"

#include "pico_config.h"

size_t status_json_build(char *buf, size_t buf_len, const frame_buffer_t *fb,
                          bool synced, int64_t last_sync_offset_us, int64_t last_sync_delay_us,
                          uint32_t uptime_s, int64_t now_us, uint32_t frames_dropped_presync) {
    pico_unique_board_id_t id;
    pico_get_unique_board_id(&id);
    char id_hex[2 * PICO_UNIQUE_BOARD_ID_SIZE_BYTES + 1];
    for (int i = 0; i < PICO_UNIQUE_BOARD_ID_SIZE_BYTES; i++) {
        snprintf(&id_hex[i * 2], 3, "%02x", id.id[i]);
    }

    int n = snprintf(buf, buf_len,
        "{"
        "\"device_name\":\"%s\","
        "\"pixel_count\":%d,"
        "\"target_fps\":45,"
        "\"firmware_version\":\"1.0.0\","
        "\"uptime_s\":%lu,"
        "\"clock\":%.6f,"
        "\"synced\":%s,"
        "\"sync\":{\"offset_us\":%lld,\"delay_us\":%lld},"
        "\"queue\":{\"depth\":%u,\"capacity\":%d,\"free_slots\":%u},"
        "\"stats\":{"
          "\"frames_received\":%u,"
          "\"frames_shown\":%u,"
          "\"frames_dropped_late\":%u,"
          "\"frames_dropped_queue_full\":%u,"
          "\"frames_rejected_bad_payload\":%u,"
          "\"frames_dropped_presync\":%u"
        "}"
        "}",
        id_hex,
        PICO_MAX_PIXELS_TOTAL, /* capacity ceiling, not a configured count - see docs/docs/pico-device.md */
        (unsigned long)uptime_s,
        now_us / 1e6,
        synced ? "true" : "false",
        (long long)last_sync_offset_us, (long long)last_sync_delay_us,
        frame_buffer_depth(fb), PICO_FRAME_SLOT_COUNT, frame_buffer_free_slots(fb),
        fb->frames_received, fb->frames_shown, fb->frames_dropped_late, fb->frames_dropped_queue_full,
        fb->frames_rejected_bad_payload, frames_dropped_presync);

    if (n < 0 || (size_t)n >= buf_len) return 0;
    return (size_t)n;
}
