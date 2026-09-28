# Pico 2 W device server - see docs/docs/pico-device.md for the design this
# implements, and docs/docs/network-pixel-protocol.md for the wire protocol.
#
# Needs PICO_SDK_PATH set to a local checkout of the Pico SDK (not vendored
# in this repo - see docs/docs/pico-device.md, "build & flash").
#
#   export PICO_SDK_PATH=/path/to/pico-sdk
#   cp wifi_secrets.h.example wifi_secrets.h   # then fill in the real values
#   mkdir build && cd build
#   cmake -DPICO_BOARD=pico2_w ..
#   make -j4
#   # flash build/gridmas-pico.uf2 by dragging it onto the RPI-RP2 mass
#   # storage device shown while holding BOOTSEL at power-on

cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(gridmas_pico C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(gridmas-pico
    src/main.c
    src/core/frame_buffer.c
    src/core/http_parser.c
    src/core/sntp_offset.c
    src/core/ws_handshake.c
    src/hw/wifi.c
    src/hw/http_server.c
    src/hw/ws_frame_server.c
    src/hw/sntp_client.c
    src/hw/status_json.c
    src/hw/ws2812_output.c
)

pico_generate_pio_header(gridmas-pico ${CMAKE_CURRENT_LIST_DIR}/src/hw/ws2812.pio)

# `.` (not just `src`) so wifi_secrets.h and lwipopts.h, which live at the
# project root next to this file per docs/docs/pico-device.md's setup steps,
# resolve as plain #include "wifi_secrets.h" from anywhere under src/.
target_include_directories(gridmas-pico PRIVATE src .)

target_link_libraries(gridmas-pico
    pico_stdlib
    pico_multicore
    pico_cyw43_arch_lwip_threadsafe_background
    pico_unique_id
    hardware_pio
    hardware_dma
    hardware_watchdog
)

pico_enable_stdio_usb(gridmas-pico 1)
pico_enable_stdio_uart(gridmas-pico 0)

pico_add_extra_outputs(gridmas-pico)
