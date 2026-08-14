#!/usr/bin/env bash
# Build a badgeware simulator variant and stage it for the host page.
#
#   tools/build.sh [board] [async]
#     board: tufty2350 (default) | badger2350 | blinky2350
#            | tufty2350-batteries (the runtime frozen in; see README)
#     async: asyncify-fast (default) | jspi
#
# Activates the Emscripten SDK if emcc isn't already on PATH (looking for a
# sibling ../emsdk or $EMSDK), initialises the submodules the build needs,
# builds mpy-cross, configures + builds the variant, then drops the host page
# (host/index.html) into the build directory so it's a self-contained, servable
# site.
set -euo pipefail

BOARD="${1:-${BADGEWARE_BOARD:-tufty2350}}"
ASYNC="${2:-${BADGEWARE_ASYNC:-asyncify-fast}}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

jobs() { getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4; }

# Activate emscripten if emcc isn't already on PATH.
if ! command -v emcc >/dev/null 2>&1; then
    for env in "$ROOT/../emsdk/emsdk_env.sh" "${EMSDK:-}/emsdk_env.sh"; do
        if [ -n "$env" ] && [ -f "$env" ]; then
            # shellcheck disable=SC1090
            source "$env" >/dev/null
            break
        fi
    done
fi
if ! command -v emcc >/dev/null 2>&1; then
    echo "error: emcc not found. Install/activate the Emscripten SDK, or put it at ../emsdk." >&2
    exit 1
fi

# Submodules this build needs (rather than a full recursive clone of MicroPython).
git submodule update --init micropython picovector-micropython
git -C picovector-micropython submodule update --init
git -C micropython submodule update --init lib/micropython-lib

# Host mpy-cross for the frozen manifest.
make -C micropython/mpy-cross -j"$(jobs)"

VARIANT_DIR="$ROOT/variants/badgeware-$BOARD"
if [ ! -f "$VARIANT_DIR/mpconfigvariant.cmake" ]; then
    echo "error: unknown board '$BOARD' (no $VARIANT_DIR)" >&2
    exit 1
fi

BUILD="build-$BOARD-$ASYNC"

# The shared cmake rules don't track config headers as dependencies of the qstr
# and frozen-content generators, so an incremental build after an mpconfig*.h
# change can desync those generated tables (e.g. "undeclared MP_QSTR_sysname",
# or "redefinition of MP_QSTR_machine" between the qstr and frozen pools). If a
# config header changed since this build was configured, wipe the build dir so
# the generated tables regenerate consistently.
if [ -f "$BUILD/CMakeCache.txt" ] && \
   [ -n "$(find variants -name '*.h' -newer "$BUILD/CMakeCache.txt" 2>/dev/null)" ]; then
    echo "config header changed since last build; clean rebuild for consistent qstr/frozen tables"
    rm -rf "$BUILD"
fi

emcmake cmake -B "$BUILD" -S micropython/ports/webassembly \
    -DMICROPY_VARIANT_DIR="$VARIANT_DIR" \
    -DBADGEWARE_ASYNC="$ASYNC"

cmake --build "$BUILD" -j"$(jobs)"

# Drop the host page into the build output so $BUILD is a self-contained site
# (micropython.mjs + micropython.wasm + index.html). host/ stays source-only.
cp "$ROOT/host/index.html" "$BUILD/index.html"

echo
echo "Built '$BOARD' ($ASYNC) -> $BUILD/ (micropython.mjs + .wasm + index.html)"
echo "Serve it:  python3 -m http.server -d $BUILD 8000"
echo "Then open: http://localhost:8000/"
