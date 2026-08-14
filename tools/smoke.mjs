// Check a batteries-included build runs a badge app with nothing staged around it.
//
//   node tools/smoke.mjs build-tufty2350-batteries-jspi/micropython.mjs
//
// Imports the frozen runtime, draws a frame and reads the framebuffer back. Nothing here
// touches the filesystem or a canvas: if this passes under plain node, the artifact is
// self-contained, which is the whole claim the variant makes.
//
// Exits non-zero on any failure, so CI can gate on it.

import { readFile } from "node:fs/promises"
import { pathToFileURL } from "node:url"
import { resolve } from "node:path"

const built = process.argv[2]
if (!built) {
  console.error("usage: node tools/smoke.mjs <path to micropython.mjs>")
  process.exit(2)
}

// A jspi build suspends through WebAssembly.Suspending, and without it emscripten's own
// check fires from somewhere deep in the generated module ("JSPI not supported by current
// environment"). Say which node this needs instead, and say it before anything loads.
//
// Only for a jspi build: an asyncify one runs anywhere, and refusing it here would be a
// requirement it does not have. The module announces which it is as it loads, which is
// too late, so the announcement is read out of the file first.
//
// The flag is not a portable answer either: node 24 and earlier want
// --experimental-wasm-jspi, and node 26 dropped it as a bad option, JSPI being on by
// default there.
const backend = /__MICROPYTHON_ASYNC__ = "([a-z-]+)"/.exec(
  await readFile(resolve(built), "utf8"))
if (backend?.[1] === "jspi" && typeof WebAssembly.Suspending !== "function") {
  console.error(
    `this node (${process.version}) has no JSPI, which a jspi build needs.\n` +
    "Use node 25 or newer, where it is on by default; on node 22-24 run node with " +
    "--experimental-wasm-jspi. An asyncify or asyncify-fast build needs none of this.")
  process.exit(2)
}

const { loadMicroPython } = await import(pathToFileURL(resolve(built)).href)

// The display driver hands its framebuffer to the host on update(); headless, it goes
// nowhere. Without these the first flip is a call to an undefined global.
globalThis.blitrgba = () => {}
globalThis.backlight = () => {}
globalThis.sim_buttons = () => 0

const mp = await loadMicroPython({
  stdout: (line) => process.stdout.write(line + "\n"),
  stderr: (line) => process.stderr.write(line + "\n"),
  linebuffer: true,
  heapsize: 64 * 1024 * 1024,
})

// Every runPython returns a promise under both async backends, so a bare try/catch here
// would miss a Python exception entirely and report success.
try {
  await mp.runPython(`
import os

# The one import that has to be enough: it injects badge, screen, image, tween, color
# and the buttons into builtins.
import badgeware

assert badge is not None, "no badge"
assert BUTTON_A is not None and BUTTON_HOME is not None, "no buttons"
assert tween.LINEAR is not None, "no tween"

fonts = os.listdir("/rom/fonts")
assert len(fonts) > 20, "the fonts were not embedded: %s" % fonts
assert font.sins is not None, "the default font did not load"

badge.mode(HIRES | VSYNC)
screen.antialias = image.X4
badge.default_clear = None
screen.pen = color.rgb(255, 0, 0)
screen.rectangle(0, 0, 320, 240)

# Read before update(), which clears afterwards.
raw = screen.raw
assert len(raw) == 320 * 240 * 4, "framebuffer is %d bytes" % len(raw)
assert tuple(raw[0:4]) == (255, 0, 0, 255), "wrong first pixel: %s" % (tuple(raw[0:4]),)

print("ok: runtime frozen in, %d fonts embedded, %d bytes of framebuffer"
      % (len(fonts), len(raw)))
`)
} catch (error) {
  console.error(error.message || error)
  process.exit(1)
}
