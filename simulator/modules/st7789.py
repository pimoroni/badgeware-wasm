# Pure-Python st7789 display shim for the Badgeware WASM simulator.
#
# A drop-in replacement for the Tufty 2350 st7789.ST7789 driver. Instead of
# driving a real panel it owns an RGBA framebuffer and blits it to the host
# canvas. The ST7789 instance *is* the framebuffer: it subclasses bytearray, so
# unmodified badgeware can do
#
#     image(display.WIDTH, display.HEIGHT, memoryview(display))
#
# and picovector rasterises straight into it. update() ships the framebuffer to
# the host by address (zero-copy) via the host-provided js.blitrgba(addr, w, h),
# which reads Module.HEAPU8 at that address and paints the canvas.

import js
import uctypes
import time

_WIDTH_HIRES = const(320)
_HEIGHT_HIRES = const(240)
_WIDTH_LORES = const(160)
_HEIGHT_LORES = const(120)
# Always allocate the hires framebuffer; lores draws into the first quarter.
_FB_BYTES = const(_WIDTH_HIRES * _HEIGHT_HIRES * 4)


class ST7789(bytearray):
    def __init__(self, *args, **kwargs):
        # Allocate the RGBA framebuffer (the instance itself).
        super().__init__(_FB_BYTES)
        # Its heap address is stable for the object's lifetime (we never resize),
        # so cache it for the per-frame blit.
        self._addr = uctypes.addressof(self)
        self._set_mode(False)  # lores by default, matching the hardware driver

    def _set_mode(self, hires):
        self._hires = hires
        self.WIDTH = _WIDTH_HIRES if hires else _WIDTH_LORES
        self.HEIGHT = _HEIGHT_HIRES if hires else _HEIGHT_LORES

    # fullres(mode) - select hires (True, 320x240) or lores (False, 160x120).
    def fullres(self, mode):
        self._set_mode(bool(mode))

    # update([fullres]) - flip the framebuffer to the host canvas. The hardware
    # driver's update() takes no argument and uses the mode set by fullres(); an
    # optional argument is accepted as a convenience and updates the mode.
    def update(self, fullres=None):
        if fullres is not None:
            self._set_mode(bool(fullres))
        js.blitrgba(self._addr, self.WIDTH, self.HEIGHT)
        # Hand the event loop a turn so the canvas paints and input is delivered,
        # mirroring the C driver's post-flip emscripten_sleep(6).
        time.sleep_ms(6)

    # backlight(value) - 0.0..1.0, forwarded to the host if it wants to dim.
    def backlight(self, value):
        setbl = getattr(js, "backlight", None)
        if setbl is not None:
            setbl(value)

    # Interface parity with the hardware driver; no effect in the simulator.
    def set_vsync(self, sync):
        pass

    def command(self, reg, data):
        pass

    def set_max_pio_clock(self, value):
        pass

    def set_framerate(self, value):
        pass
