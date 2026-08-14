// Check a batteries-included build runs a badge app with nothing staged around it.
//
//   node tools/smoke.mjs build-tufty2350-batteries-jspi/micropython.mjs
//
// Imports the frozen runtime, draws a frame and reads the framebuffer back. Nothing here
// touches the filesystem or a canvas: if this passes under plain node, the artifact is
// self-contained, which is the whole claim the variant makes.
//
// Exits non-zero on any failure, so CI can gate on it.

import { pathToFileURL } from "node:url"
import { resolve } from "node:path"

const built = process.argv[2]
if (!built) {
  console.error("usage: node tools/smoke.mjs <path to micropython.mjs>")
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
