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
  variants/badgeware-tufty2350/
    mpconfigvariant.cmake      build config (async backend + picovector + manifest)
    mpconfigvariant.h          MicroPython feature config for the board
    manifest.py                frozen Python modules
  simulator/modules/          pure-Python simulated hardware:
    st7789.py                   display: a bytearray framebuffer picovector draws
                                into, blitted to the host canvas by address
    machine.py                  Pin / PWM / ADC / I2C / RTC
    picovector_io.py            button input
    ...                         networking + firmware shims (fetch, wifi, ...)
  .github/workflows/build.yml CI: builds the asyncify-fast + jspi variants
```

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

# Configure + build (async backend: asyncify-fast [default] or jspi)
emcmake cmake -B build -S micropython/ports/webassembly \
  -DMICROPY_VARIANT_DIR=$PWD/variants/badgeware-tufty2350 \
  -DBADGEWARE_ASYNC=asyncify-fast
cmake --build build -j

# -> build/micropython.mjs + build/micropython.wasm
```

[pv]: https://github.com/pimoroni/picovector-micropython
