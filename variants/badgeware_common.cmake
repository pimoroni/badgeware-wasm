# Shared build config for the badgeware simulator variants (tufty2350,
# badger2350, blinky2350). Each board's mpconfigvariant.cmake includes this; the
# only per-board differences are the board name (mpconfigvariant.h) and the
# frozen display driver (manifest.py).
#
# Uses MICROPY_VARIANT_DIR (set by the port to the board's variant directory) so
# a single fragment serves every board.

# --- async backend -----------------------------------------------------------
# Default asyncify-fast (small, ~2.5x faster than plain asyncify); override with
# -DBADGEWARE_ASYNC=jspi or =asyncify. Reuses the port's own variant fragment.
if(NOT BADGEWARE_ASYNC)
    set(BADGEWARE_ASYNC asyncify-fast)
endif()
include(${MICROPY_PORT_DIR}/variants/${BADGEWARE_ASYNC}/mpconfigvariant.cmake)

# --- picovector graphics (USER_C_MODULE) -------------------------------------
set(CMAKE_CXX_STANDARD 17)
get_filename_component(_badgeware_root "${MICROPY_VARIANT_DIR}/../.." ABSOLUTE)
set(USER_C_MODULES ${_badgeware_root}/picovector_wasm.cmake)

# --- frozen python -----------------------------------------------------------
# Expose the repo root to the manifest as $(BADGEWARE_DIR).
set(MICROPY_MANIFEST_BADGEWARE_DIR ${_badgeware_root})
set(MICROPY_FROZEN_MANIFEST ${MICROPY_VARIANT_DIR}/manifest.py)
