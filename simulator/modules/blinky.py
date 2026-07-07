# Pure-Python blinky display shim for the Badgeware WASM simulator (Pimoroni
# Blinky 2350, a 39x26 RGB LED matrix).
#
# A drop-in replacement for the hardware blinky.Blinky driver. It exposes a
# 39x26 RGBA framebuffer via the buffer protocol, so unmodified badgeware does
# image(display.WIDTH, display.HEIGHT, memoryview(display)) and picovector
# rasterises into it.
#
# The Blinky matrix is white LEDs only - 8-bit greyscale (per-LED brightness).
# Like the hardware driver, update() converts the picovector RGBA framebuffer to
# the panel's format: picovector's monochrome() filter reduces it to 8-bit
# luminance (R=G=B) at C speed, which the host then paints as white LED
# intensity. The framebuffer is blitted by address (zero-copy) via
# js.blitrgba(addr, w, h).

import js
import uctypes
import time
import picovector

WIDTH = const(39)
HEIGHT = const(26)
_FB_BYTES = const(WIDTH * HEIGHT * 4)


class Blinky(bytearray):
    def __init__(self, *args, **kwargs):
        super().__init__(_FB_BYTES)
        self._addr = uctypes.addressof(self)
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self._brightness = 1.0
        # A picovector view of our own framebuffer, for the monochrome pass.
        self._img = picovector.image(WIDTH, HEIGHT, memoryview(self))

    def clear(self):
        # Zero the LED framebuffer.
        for i in range(_FB_BYTES):
            self[i] = 0

    def update(self):
        self._img.monochrome()   # RGBA -> 8-bit greyscale (white LED intensity)
        js.blitrgba(self._addr, WIDTH, HEIGHT)
        time.sleep_ms(6)

    def set_brightness(self, value):
        self._brightness = max(0.0, min(1.0, value))
        setbl = getattr(js, "backlight", None)
        if setbl is not None:
            setbl(self._brightness)

    def get_brightness(self):
        return self._brightness

    def adjust_brightness(self, delta):
        self.set_brightness(self._brightness + delta)
