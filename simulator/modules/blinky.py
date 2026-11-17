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
_MAX_SUPERSAMPLE = const(4)
_FB_BYTES = const(WIDTH * HEIGHT * 4)


class Blinky(bytearray):
    def __init__(self, *args, **kwargs):
        super().__init__(_FB_BYTES * _MAX_SUPERSAMPLE * _MAX_SUPERSAMPLE)
        self._addr = uctypes.addressof(self)
        self._panel = bytearray(_FB_BYTES)
        self._panel_addr = uctypes.addressof(self._panel)
        self._brightness = 1.0
        self.set_supersample(1)

    def clear(self):
        # Zero the LED framebuffer.
        for i in range(len(self)):
            self[i] = 0

    def set_supersample(self, scale):
        if scale not in (1, 2, 4):
            scale = 1
        self.SCALE = scale
        self.WIDTH = WIDTH * scale
        self.HEIGHT = HEIGHT * scale
        # A picovector view of our own framebuffer, for the monochrome pass.
        self._img = picovector.image(self.WIDTH, self.HEIGHT, memoryview(self))

    def _downsample(self):
        scale = self.SCALE
        stride = self.WIDTH * 4
        divisor = scale * scale
        source = memoryview(self)
        panel = self._panel
        i = 0
        for y in range(HEIGHT):
            for x in range(WIDTH):
                total = 0
                for sy in range(scale):
                    offset = (y * scale + sy) * stride + x * scale * 4
                    for sx in range(scale):
                        total += source[offset + sx * 4]
                v = total // divisor
                panel[i] = panel[i + 1] = panel[i + 2] = v
                panel[i + 3] = 255
                i += 4

    def update(self):
        self._img.monochrome()   # RGBA -> 8-bit greyscale (white LED intensity)
        if self.SCALE == 1:
            js.blitrgba(self._addr, WIDTH, HEIGHT)
        else:
            self._downsample()
            js.blitrgba(self._panel_addr, WIDTH, HEIGHT)
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
