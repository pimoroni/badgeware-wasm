# Badgeware WASM integration of picovector-micropython as a USER_C_MODULE.
#
# Consumes picovector-micropython's own cmake directly (single source of truth
# for the generated binding / decoder source list) and adapts it for the
# emscripten target: the RP2 hardware interpolator is pico-sdk only, so build
# the portable C++ rasteriser instead, and relax the webassembly port's -Werror
# for the third-party C++.
#
# Wired in via -DUSER_C_MODULES=<this file> (the badgeware-tufty2350 variant
# sets it). Included from py/usermod.cmake, i.e. after project(), so the
# usermod_picovector target exists immediately after the include below.

# Off-target: no pico-sdk hardware_interp. Set before the include so the
# option() in picovector_micropython.cmake honours it (CMP0077).
set(PV_HARDWARE_INTERP OFF)

include(${CMAKE_CURRENT_LIST_DIR}/picovector-micropython/picovector_micropython.cmake)

# picovector is third-party C++ that trips the port's -Werror (float-conversion,
# missing-override, ...). Route the relaxation and the no-exceptions/no-rtti
# build (picovector never throws; its std containers use the MicroPython heap
# allocator) through the picovector target's C++ compile only.
# picovector's allocator (runtime/mp_allocator.hpp) uses m_malloc_no_scan for
# pointer-free data, a Pimoroni-fork GC API. Upstream MicroPython has no
# per-block no-scan allocation (the mark phase scans every reachable block), so
# map it onto the regular scanned allocator: correct (conservative), at the
# minor cost of the GC scanning pixel buffers.
target_compile_definitions(usermod_picovector INTERFACE m_malloc_no_scan=m_malloc)

# native/image_jpeg.cpp also includes bitbank2 JPEGDEC.h, so it needs the same
# plain-libc platform hint as the jpegdec library target below.
target_compile_definitions(usermod_picovector INTERFACE __LINUX__)

target_compile_options(usermod_picovector INTERFACE
    $<$<COMPILE_LANGUAGE:CXX>:-Wno-error;-fno-exceptions;-fno-rtti>
)

# bitbank2 JPEGDEC falls back to <Arduino.h> unless a known platform macro is
# set; picovector only sets PICO_BUILD on pico. Tell it this is a plain-libc
# target so it uses <stdlib.h>/<stdint.h> instead.
if(TARGET jpegdec)
    target_compile_definitions(jpegdec PRIVATE __LINUX__)
endif()
