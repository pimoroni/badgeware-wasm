#!/usr/bin/env bash
# Build a badgeware simulator variant and stage it for the host page.
#
#   tools/build.sh [board] [async]
#     board: tufty2350 (default) | badger2350 | blinky2350
#     async: asyncify-fast (default) | jspi
#
# Activates the Emscripten SDK if emcc isn't already on PATH (looking for a
# sibling ../emsdk or $EMSDK), initialises the submodules the build needs,
# builds mpy-cross, then configures + builds the variant and copies
# micropython.mjs/.wasm into host/ so you can serve it.
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
emcmake cmake -B "$BUILD" -S micropython/ports/webassembly \
    -DMICROPY_VARIANT_DIR="$VARIANT_DIR" \
    -DBADGEWARE_ASYNC="$ASYNC"
cmake --build "$BUILD" -j"$(jobs)"

# Stage for the host page.
mkdir -p host
cp "$BUILD/micropython.mjs" "$BUILD/micropython.wasm" host/

echo
echo "Built '$BOARD' ($ASYNC) -> host/micropython.mjs (+ .wasm)"
echo "Serve it:  python3 -m http.server -d host 8000"
echo "Then open: http://localhost:8000/"
