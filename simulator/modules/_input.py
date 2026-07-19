# Pure-Python `_input` input shim for the Badgeware WASM simulator.
#
# Mirrors the C input module: poll() samples the (simulated) button GPIOs via the
# machine shim, and the module exposes frame-stable held/pressed/released/changed
# button sets plus millisecond ticks. Button GPIOs are active-low.

import machine
import time

BUTTON_HOME = const(0x20)
BUTTON_A = const(0x10)
BUTTON_B = const(0x08)
BUTTON_C = const(0x04)
BUTTON_UP = const(0x02)
BUTTON_DOWN = const(0x01)

# Button bit -> GPIO (see tufty2350/board/pins.csv).
_GPIO = (
    (BUTTON_A, 7),
    (BUTTON_B, 9),
    (BUTTON_C, 10),
    (BUTTON_UP, 11),
    (BUTTON_DOWN, 6),
    (BUTTON_HOME, 22),
)

_buttons = 0
_changed = 0
_ticks = 0
_last_ticks = 0


def poll():
    """Sample the buttons and update the frame-stable input and tick values."""
    global _buttons, _changed, _ticks, _last_ticks
    b = 0
    for bit, gpio in _GPIO:
        if not machine.Pin(gpio).value():   # active-low: 0 = pressed
            b |= bit
    _changed = b ^ _buttons
    _buttons = b
    _last_ticks = _ticks
    _ticks = time.ticks_ms()


# Button bit -> GPIO in the C module's reported order (HOME, A, B, C, UP, DOWN).
_ORDER = (
    (BUTTON_HOME, 22),
    (BUTTON_A, 7),
    (BUTTON_B, 9),
    (BUTTON_C, 10),
    (BUTTON_UP, 11),
    (BUTTON_DOWN, 6),
)


def _button_tuple(mask):
    # Return the board Pin objects for the set buttons, matching the C _input
    # module (which yields machine.Pin.board.<button>). badge.pressed() tests
    # `pin in _input.pressed`; Pin compares by GPIO id (see machine.Pin).
    return tuple(machine.Pin(gpio) for bit, gpio in _ORDER if mask & bit)


# Dynamic module attributes (PEP 562), matching the C module's delegation.
def __getattr__(name):
    if name == "ticks":
        return _ticks
    if name == "ticks_delta":
        return _ticks - _last_ticks
    if name == "held":
        return _button_tuple(_buttons)
    if name == "pressed":
        return _button_tuple(_buttons & _changed)
    if name == "released":
        return _button_tuple(~_buttons & _changed)
    if name == "changed":
        return _button_tuple(_changed)
    raise AttributeError(name)
