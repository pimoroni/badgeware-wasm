# Badgeware simulator variant for the Pimoroni Tufty 2350 (cmake, out-of-tree).
#
# Built against the webassembly-cmake MicroPython port via:
#   emcmake cmake -S micropython/ports/webassembly \
#     -DMICROPY_VARIANT_DIR=<badgeware-wasm>/variants/badgeware-tufty2350
#
# It layers picovector-micropython (graphics, a C++ USER_C_MODULE) on top of one
# of the port's suspend-capable async backends. The simulated machine / display
# / input are pure-Python frozen modules (see simulator/), so there are no
# badgeware C sources here.

# --- async backend -----------------------------------------------------------
# How MicroPython suspends to the JS event loop. Default to asyncify-fast (small,
# ~2.5x faster than plain asyncify); override with -DBADGEWARE_ASYNC=jspi or
# =asyncify. Reuses the port's own variant fragment for the backend flags.
if(NOT BADGEWARE_ASYNC)
    set(BADGEWARE_ASYNC asyncify-fast)
endif()
include(${MICROPY_PORT_DIR}/variants/${BADGEWARE_ASYNC}/mpconfigvariant.cmake)

# --- picovector graphics (USER_C_MODULE) -------------------------------------
set(CMAKE_CXX_STANDARD 17)
get_filename_component(_badgeware_root "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
set(USER_C_MODULES ${_badgeware_root}/picovector_wasm.cmake)

# --- frozen python (simulator modules + shims) -------------------------------
# Expose the badgeware repo root to the manifest as $(BADGEWARE_DIR) (all
# MICROPY_MANIFEST_* cmake vars become makemanifest path substitutions).
set(MICROPY_MANIFEST_BADGEWARE_DIR ${_badgeware_root})
set(MICROPY_FROZEN_MANIFEST ${CMAKE_CURRENT_LIST_DIR}/manifest.py)
