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
    badgeware-tufty2350-batteries/
                                Tufty, with the badgeware runtime frozen in
  simulator/
    manifest_common.py         shared frozen modules (machine, input, shims, stdlib)
    modules/                   pure-Python simulated hardware:
      st7789.py                 Tufty:  320x240 RGB LCD
      ssd1680.py                Badger: 264x176 e-ink
      blinky.py                 Blinky: 39x26 RGB LED matrix
      machine.py                Pin / PWM / ADC / I2C / RTC
      picovector_io.py          button input
      powman.py                 sleep / wake, which a tab cannot do
      pcf85063a.py              the RTC, read off the host clock
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

### Batteries included

The ordinary builds leave the badgeware runtime, its peripheral shims and the
fonts on the filesystem, where whoever is using the simulator can read and edit
them. `tufty2350-batteries` freezes all three into the image instead, so a
caller that only wants to *run* a badge app has nothing to stage:

```sh
tools/build.sh tufty2350-batteries jspi
```

```js
const mp = await loadMicroPython({ url: "micropython.wasm" })
globalThis.blitrgba = () => {}          // headless: swallow the flip
await mp.runPython(`
import badgeware                        # badge, screen, image, tween, BUTTON_*
badge.mode(HIRES | VSYNC)
screen.pen = color.rgb(255, 0, 0)
screen.rectangle(0, 0, 320, 240)
print(len(screen.raw))                  # 307200 bytes of RGBA
`)
```

Nothing needs a canvas, so it runs under plain `node`. The badgeware package
and the fonts are the firmware's, read from a checkout of it rather than copied
here: clone `tufty2350` beside this repo, or configure with
`-DBADGEWARE_FIRMWARE_DIR=/path/to/tufty2350`. JSPI is this variant's default,
the fonts put ~430KB on the wasm, and everything else is unchanged - the two
Tufty variants build side by side.

`tools/smoke.mjs` is the check that the claim holds - it imports the runtime,
draws a frame and reads the framebuffer back with nothing staged:

```sh
node tools/smoke.mjs build-tufty2350-batteries-jspi/micropython.mjs
```

**JSPI needs a recent runtime.** A jspi build suspends through
`WebAssembly.Suspending`, and without it emscripten stops with "JSPI not
supported by current environment". That means node 25 or newer (node 22-24 want
`--experimental-wasm-jspi`, which node 26 rejects as a bad option), or Chrome
137+ in a browser. Where that is awkward - an older CI runner, a browser you do
not control - build the same variant against a backend that needs none of it:

```sh
tools/build.sh tufty2350-batteries asyncify-fast
```

Everything above still applies; the wasm is 1.7MB against jspi's 1.1MB, and
slower to suspend. `-DBADGEWARE_ASYNC` overrides the variant's default either
way, and `tools/smoke.mjs` only asks for JSPI of a build that uses it.

### Fetching a built one

Publishing a release attaches this build to it as
`badgeware-tufty2350-batteries-jspi.zip`, so another repository's CI can pin a
copy instead of building emscripten of its own:

```sh
gh release download <tag> --repo pimoroni/badgeware-wasm \
  --pattern 'badgeware-tufty2350-batteries-jspi.zip'
unzip -q badgeware-tufty2350-batteries-jspi.zip -d runtime
node your-driver.mjs runtime/micropython.mjs
```

The two files stay together and keep their names: the generated
`micropython.mjs` looks for `micropython.wasm` beside itself, so splitting or
renaming them means passing `url` to `loadMicroPython` to put it right again.

While this repository is private a plain `curl` of the download URL will not do:
`gh` needs a token with read access to it, which in another repository's Actions
means a PAT or a deploy key in a secret, `GITHUB_TOKEN` being scoped to the
repository running the job.

[pv]: https://github.com/pimoroni/picovector-micropython
