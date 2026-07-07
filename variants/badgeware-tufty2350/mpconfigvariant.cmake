# Badgeware simulator variant for the Pimoroni Tufty 2350 (320x240 ST7789 LCD).
# Built against the webassembly-cmake MicroPython port via:
#   emcmake cmake -S micropython/ports/webassembly \
#     -DMICROPY_VARIANT_DIR=<badgeware-wasm>/variants/badgeware-tufty2350
include(${CMAKE_CURRENT_LIST_DIR}/../badgeware_common.cmake)
