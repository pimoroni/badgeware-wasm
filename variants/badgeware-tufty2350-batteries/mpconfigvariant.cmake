# Tufty 2350 with the badgeware runtime built in, for running a badge app with nothing
# staged around it.
#
# The ordinary tufty2350 variant leaves the badgeware package, its peripheral shims and
# the fonts on the filesystem, where the simulator's user can read and edit them. That is
# the point of it, and this variant does not change it: everything here is additional, and
# the two build side by side.
#
# What that costs a headless caller is a staging step - copy the package into MEMFS at the
# right two paths, write the powman and pcf85063a shims, copy 35 fonts - before any app
# can be imported. Frozen in, `import badgeware` is all of it, so a CI job needs the
# artifact and nothing else.
#
#   tools/build.sh tufty2350-batteries jspi
#
# The badgeware package and the fonts belong to the firmware and are read from a checkout
# of it, so they cannot drift from the badge: point -DBADGEWARE_FIRMWARE_DIR at one, or
# leave it and a sibling ../../tufty2350 is used.

# JSPI by default: this variant exists to be driven from node, where stack switching is
# available and the wasm is 40% of asyncify's. `tools/build.sh` still takes an override.
if(NOT BADGEWARE_ASYNC)
    set(BADGEWARE_ASYNC jspi)
endif()

include(${CMAKE_CURRENT_LIST_DIR}/../badgeware_common.cmake)

# Tufty's reflective LCD renders pure black/white poorly; flag the generated picovector
# colour table (generated/color.cpp) to use tinted ink/paper.
set(BADGEWARE_TUFTY ON)

# --- the firmware's own files ------------------------------------------------
if(NOT BADGEWARE_FIRMWARE_DIR)
    get_filename_component(BADGEWARE_FIRMWARE_DIR
                           "${MICROPY_VARIANT_DIR}/../../../../tufty2350" ABSOLUTE)
endif()

set(_badgeware_pkg ${BADGEWARE_FIRMWARE_DIR}/modules/common/badgeware)
set(_badgeware_fonts ${BADGEWARE_FIRMWARE_DIR}/romfs/fonts)
if(NOT EXISTS ${_badgeware_pkg}/badge.py)
    message(FATAL_ERROR
        "no badgeware package at ${_badgeware_pkg}.\n"
        "This variant freezes the firmware's own runtime, so it needs a tufty2350 "
        "checkout: clone one beside this repo, or configure with "
        "-DBADGEWARE_FIRMWARE_DIR=/path/to/tufty2350")
endif()
if(NOT EXISTS ${_badgeware_fonts})
    message(FATAL_ERROR "no fonts at ${_badgeware_fonts}")
endif()

# Read by manifest.py as $(FIRMWARE_DIR).
set(MICROPY_MANIFEST_FIRMWARE_DIR ${BADGEWARE_FIRMWARE_DIR})

# The fonts are data and not modules, so the manifest cannot carry them: picovector's
# font.load searches /rom/fonts first, and emscripten can put them there at link time.
# SHELL: keeps the flag and its argument together, which CMake would otherwise split.
list(APPEND MICROPY_PORT_LINK_OPTS
     "SHELL:--embed-file ${_badgeware_fonts}@/rom/fonts")
