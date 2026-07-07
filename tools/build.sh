#!/usr/bin/env bash
# Build the badgeware-tufty2350 simulator and stage it for the host page.
#
#   tools/build.sh [asyncify-fast|jspi]     (default: asyncify-fast)
#
# Activates the Emscripten SDK if emcc isn't already on PATH (looking for a
# sibling ../emsdk or $EMSDK), initialises the submodules the build needs,
# builds mpy-cross, then configures + builds the variant and copies
# micropython.mjs/.wasm into host/ so you can serve it.
set -euo pipefail

ASYNC="${1:-${BADGEWARE_ASYNC:-asyncify-fast}}"

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

BUILD="build-$ASYNC"
emcmake cmake -B "$BUILD" -S micropython/ports/webassembly \
    -DMICROPY_VARIANT_DIR="$ROOT/variants/badgeware-tufty2350" \
    -DBADGEWARE_ASYNC="$ASYNC"
cmake --build "$BUILD" -j"$(jobs)"

# Stage for the host page.
mkdir -p host
cp "$BUILD/micropython.mjs" "$BUILD/micropython.wasm" host/

echo
echo "Built '$ASYNC' -> host/micropython.mjs (+ .wasm)"
echo "Serve it:  python3 -m http.server -d host 8000"
echo "Then open: http://localhost:8000/"
