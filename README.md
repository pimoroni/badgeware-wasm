# badgeware-wasm

The Badgeware WebAssembly simulator: MicroPython + [picovector][pv] graphics
compiled to WASM, with a pure-Python simulation of the Tufty 2350 hardware
(display, buttons, machine peripherals). It runs unmodified badgeware firmware
in the browser.

## Layout

```
badgeware-wasm/
  micropython/                submodule -> pimoroni/micropython @ webassembly-cmake
                              (adds a CMake build to the webassembly port)
  picovector-micropython/     submodule -> pimoroni/picovector-micropython
                              (graphics, consumed as a USER_C_MODULE)
  picovector_wasm.cmake       badgeware's USER_C_MODULE glue (picovector for emscripten)
  variants/
    badgeware_common.cmake     shared build config (async backend + picovector + manifest)
    badgeware_common.h         shared MicroPython feature config
    badgeware-tufty2350/        per-board: board name + frozen display driver
    badgeware-badger2350/
    badgeware-blinky2350/
  simulator/
    manifest_common.py         shared frozen modules (machine, input, shims, stdlib)
    modules/                   pure-Python simulated hardware:
      st7789.py                 Tufty:  320x240 RGB LCD
      ssd1680.py                Badger: 264x176 e-ink
      blinky.py                 Blinky: 39x26 RGB LED matrix
      machine.py                Pin / PWM / ADC / I2C / RTC
      picovector_io.py          button input
      ...                       networking + firmware shims (fetch, wifi, ...)
  .github/workflows/build.yml CI: builds each board x async backend
```

Each display driver subclasses `bytearray` (so it *is* the framebuffer),
exposes the board's resolution + methods, and blits by address on `update()`.
Adding a board is: a display-driver module + a three-line variant directory
(board name + which display to freeze); everything else is shared.

There are **no badgeware C sources**: the simulated hardware is Python, and the
only native module is picovector (via `USER_C_MODULES`). The webassembly port
itself is unmodified upstream-style MicroPython on the `webassembly-cmake`
branch.

## How the display works

`st7789.ST7789` subclasses `bytearray`, so it *is* an RGBA framebuffer that
satisfies the buffer protocol. Unmodified firmware does
`image(display.WIDTH, display.HEIGHT, memoryview(display))` and picovector
rasterises straight into it. `display.update()` ships the framebuffer to the
host **by address** (`uctypes.addressof`), zero-copy:

```js
// the host page provides:
globalThis.blitrgba = (addr, w, h) => {
  const bytes = globalThis.Module.HEAPU8.subarray(addr, addr + w * h * 4);
  ctx.putImageData(new ImageData(new Uint8ClampedArray(bytes), w, h), 0, 0);
};
```

## Building

Requires the Emscripten SDK (`emcc`) and a host C compiler for `mpy-cross`.

```sh
git submodule update --init micropython picovector-micropython
git -C picovector-micropython submodule update --init
git -C micropython submodule update --init lib/micropython-lib

make -C micropython/mpy-cross          # host mpy-cross

# Configure + build a board (tufty2350 | badger2350 | blinky2350) and async
# backend (asyncify-fast [default] | jspi):
emcmake cmake -B build -S micropython/ports/webassembly \
  -DMICROPY_VARIANT_DIR=$PWD/variants/badgeware-tufty2350 \
  -DBADGEWARE_ASYNC=asyncify-fast
cmake --build build -j

# -> build/micropython.mjs + build/micropython.wasm
```

Or use the helper, which builds a self-contained servable site (the built
micropython.mjs/.wasm plus host/index.html) in the build directory:

```sh
tools/build.sh tufty2350             # board: tufty2350 | badger2350 | blinky2350
tools/build.sh tufty2350 jspi        # optional async backend: asyncify-fast | jspi
python3 -m http.server -d build-tufty2350-asyncify-fast 8000
# then open http://localhost:8000/
```

[pv]: https://github.com/pimoroni/picovector-micropython
