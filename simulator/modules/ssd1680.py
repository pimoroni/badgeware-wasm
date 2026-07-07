# Pure-Python ssd1680 e-ink display shim for the Badgeware WASM simulator
# (Pimoroni Badger 2350).
#
# A drop-in replacement for the hardware ssd1680.SSD1680 driver. Like the real
# driver it exposes a 264x176 RGBA framebuffer via the buffer protocol, so
# unmodified badgeware does image(display.WIDTH, display.HEIGHT, memoryview(display))
# and picovector rasterises straight into it.
#
# The Badger panel is 2-bit greyscale (4 levels). Like the hardware driver,
# update() converts the picovector RGBA framebuffer to the panel's format before
# it goes to the display: picovector's monochrome() filter does the RGBA ->
# greyscale step at C speed, then we quantise to 4 levels. The (already
# greyscale) framebuffer is then blitted to the host canvas by address (zero
# copy) via js.blitrgba(addr, w, h). The e-ink refresh-speed / busy machinery is
# a no-op: the simulated panel is never busy.

import js
import uctypes
import time
import picovector

WIDTH = const(264)
HEIGHT = const(176)
_FB_BYTES = const(WIDTH * HEIGHT * 4)


class SSD1680(bytearray):
    def __init__(self, *args, **kwargs):
        super().__init__(_FB_BYTES)
        self._addr = uctypes.addressof(self)
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self._speed = 0
        # A picovector view of our own framebuffer, for the monochrome pass.
        self._img = picovector.image(WIDTH, HEIGHT, memoryview(self))

    def update(self):
        # RGBA -> greyscale (C speed) ...
        self._img.monochrome()
        # ... then quantise to the panel's 2 bits (4 levels: 0, 85, 170, 255).
        # e-ink refreshes slowly, so this per-pixel pass is well within budget.
        mv = memoryview(self)
        for i in range(0, _FB_BYTES, 4):
            q = (mv[i] + 42) // 85 * 85
            mv[i] = mv[i + 1] = mv[i + 2] = q
        js.blitrgba(self._addr, WIDTH, HEIGHT)
        time.sleep_ms(6)   # hand the event loop a turn (host paints, input polled)

    # Interface parity with the hardware driver; no effect in the simulator.
    def speed(self, speed):
        self._speed = speed

    def blocking(self, blocking):
        pass

    def busy(self):
        return False       # the simulated panel is never busy

    def command(self, reg, data):
        pass
