# Pure-Python ssd1680 e-ink display shim for the Badgeware WASM simulator
# (Pimoroni Badger 2350).
#
# A drop-in replacement for the hardware ssd1680.SSD1680 driver. Like the real
# driver it exposes a 264x176 RGBA framebuffer via the buffer protocol, so
# unmodified badgeware does image(display.WIDTH, display.HEIGHT, memoryview(display))
# and picovector rasterises straight into it. update() blits the framebuffer to
# the host canvas by address (zero-copy) via the host-provided
# js.blitrgba(addr, w, h). The e-ink refresh-speed / busy machinery is a no-op:
# the simulated panel is never busy.

import js
import uctypes
import time

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

    def update(self):
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
