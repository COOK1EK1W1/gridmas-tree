#!/usr/bin/env bash
# Compiles and runs the host-testable core/ logic (frame_buffer, http_parser,
# sntp_offset) with the system C compiler - no Pico SDK, no CMake, no
# hardware needed. See docs/docs/pico-device.md for why this split exists.
set -euo pipefail
cd "$(dirname "$0")"

SRC=../src
CC=${CC:-cc}
CFLAGS="-std=c11 -Wall -Wextra -I$SRC"

for test in test_frame_buffer test_http_parser test_sntp_offset test_ws_handshake; do
    core_file="${test#test_}"
    "$CC" $CFLAGS -o "/tmp/$test" "$test.c" "$SRC/core/$core_file.c"
    "/tmp/$test"
done
