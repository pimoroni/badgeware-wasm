# Pure-Python `machine` shim for the Badgeware WASM simulator.
#
# Mimics the RP2350 peripherals the badgeware firmware uses (Pin, PWM, ADC, I2C,
# RTC) and bridges their state to/from the host. The host may provide optional
# globalThis functions to source inputs and observe outputs:
#
#   sim_gpio_get(id) -> 0|1|None   host-driven input (None = fall through)
#   sim_gpio_set(id, value)        last value driven by Pin.value(x)
#   sim_pwm_set(id, freq, duty)    PWM state (duty is a u16); CL0..CL3 = caselights
#   sim_adc_get(channel) -> int|None
#   sim_buttons() -> int           active-high bitmask of pressed buttons
#
# All are optional; without them the shim uses the same sensible defaults as the
# old C simulator so unmodified badgeware code still runs.

import js

# Board pin names -> GPIO, mirroring tufty2350/board/pins.csv. CHARGE_STAT lives
# on an IO expander on hardware, so it gets a synthetic id.
_BOARD_PINS = {
    "CL0": 0, "CL1": 1, "CL2": 2, "CL3": 3,
    "I2C_SDA": 4, "I2C_SCL": 5,
    "BUTTON_DOWN": 6, "BUTTON_A": 7, "BUTTON_B": 9,
    "BUTTON_C": 10, "BUTTON_UP": 11,
    "VBUS_DETECT": 12, "RTC_ALARM": 13, "BUTTON_RESET": 14,
    "BUTTON_INT": 15, "BUTTON_HOME": 22,
    "LCD_BACKLIGHT": 26,
    "VBAT_SENSE": 40, "POWER_EN": 41, "SENSE_1V1": 42, "LIGHT_SENSE": 43,
    "CHARGE_STAT": 202,
}

# Button GPIO -> bit in the input bitmask used by picovector_io.
_BUTTON_BIT = {22: 0x20, 7: 0x10, 9: 0x08, 10: 0x04, 11: 0x02, 6: 0x01}

_gpio = {}   # last value driven by Pin.value(x)
_pwm = {}    # gpio -> [freq, duty]


def _host(name):
    try:
        fn = getattr(js, name)
    except (AttributeError, KeyError):
        return None
    return fn if fn else None


def _buttons():
    fn = _host("sim_buttons")
    if fn is not None:
        v = fn()
        if v is not None:
            return int(v)
    return 0


def _gpio_get(gpio):
    fn = _host("sim_gpio_get")
    if fn is not None:
        v = fn(gpio)
        if v is not None:
            return int(v)
    bit = _BUTTON_BIT.get(gpio, 0)
    if bit:                                   # buttons are active-low
        return 0 if (_buttons() & bit) else 1
    return _gpio.get(gpio, 0)


def _gpio_set(gpio, value):
    _gpio[gpio] = 1 if value else 0
    fn = _host("sim_gpio_set")
    if fn is not None:
        fn(gpio, _gpio[gpio])


def _pwm_set(gpio, freq, duty):
    _pwm[gpio] = [freq, duty]
    fn = _host("sim_pwm_set")
    if fn is not None:
        fn(gpio, freq, duty)


def _adc_get(channel):
    fn = _host("sim_adc_get")
    if fn is not None:
        v = fn(channel)
        if v is not None:
            return int(v)
    if channel == 0:
        return 39700   # VBAT_SENSE  (~4.0V through /2 divider)
    if channel == 2:
        return 21845   # SENSE_1V1   (~1.1V reference)
    if channel == 3:
        return 40000   # LIGHT_SENSE (a comfortable mid level)
    return 0


def _pin_id(obj):
    if isinstance(obj, Pin):
        return obj.id
    if isinstance(obj, str):
        try:
            return _BOARD_PINS[obj]
        except KeyError:
            raise ValueError("unknown pin name")
    return int(obj)


class Pin:
    IN = 0
    OUT = 1
    OPEN_DRAIN = 2
    PULL_UP = 1
    PULL_DOWN = 2
    IRQ_FALLING = 4
    IRQ_RISING = 8

    class _Board:
        def __getattr__(self, name):
            try:
                return Pin(_BOARD_PINS[name])
            except KeyError:
                raise AttributeError(name)

    board = _Board()

    def __init__(self, id, mode=None, pull=None, *args, **kwargs):
        self.id = _pin_id(id)
        self.mode = mode
        self.pull = pull

    def value(self, x=None):
        if x is None:
            return _gpio_get(self.id)
        _gpio_set(self.id, 1 if x else 0)

    def on(self):
        _gpio_set(self.id, 1)

    def off(self):
        _gpio_set(self.id, 0)

    def toggle(self):
        _gpio_set(self.id, 0 if _gpio_get(self.id) else 1)

    def init(self, *args, **kwargs):
        pass

    def irq(self, *args, **kwargs):
        pass  # never fires in the simulator

    def __repr__(self):
        return "Pin(%d)" % self.id


class PWM:
    def __init__(self, pin, *args, **kwargs):
        self.id = _pin_id(pin)
        self._freq = 1000
        self._duty = 0
        _pwm_set(self.id, self._freq, self._duty)

    def freq(self, freq=None):
        if freq is None:
            return self._freq
        self._freq = int(freq)
        _pwm_set(self.id, self._freq, self._duty)

    def duty_u16(self, duty=None):
        if duty is None:
            return self._duty
        self._duty = max(0, min(65535, int(duty)))
        _pwm_set(self.id, self._freq, self._duty)

    def duty_ns(self, ns=None):
        period_ns = (1000000000 // self._freq) if self._freq else 0
        if ns is None:
            return (self._duty * period_ns // 65535) if period_ns else 0
        duty = (int(ns) * 65535 // period_ns) if period_ns else 0
        self._duty = max(0, min(65535, duty))
        _pwm_set(self.id, self._freq, self._duty)

    def deinit(self):
        self._duty = 0
        _pwm_set(self.id, self._freq, 0)

    def init(self, *args, **kwargs):
        pass

    def __repr__(self):
        return "PWM(Pin(%d), freq=%u, duty_u16=%u)" % (self.id, self._freq, self._duty)


class ADC:
    def __init__(self, source, *args, **kwargs):
        if isinstance(source, int) and 0 <= source < 8:
            self.channel = source
            self.gpio = 40 + source
        else:
            self.gpio = _pin_id(source)
            self.channel = (self.gpio - 40) if 40 <= self.gpio <= 47 else -1

    def read_u16(self):
        return _adc_get(self.channel)

    def read_uv(self):
        return _adc_get(self.channel) * 3300000 // 65535

    def __repr__(self):
        return "ADC(channel=%d, gpio=%d)" % (self.channel, self.gpio)


class I2C:
    # A stub: the simulator has no peripherals on the bus. Shimmed drivers read
    # zeros.
    def __init__(self, *args, **kwargs):
        pass

    def scan(self):
        return []

    def readfrom_mem(self, addr, memaddr, nbytes, *args, **kwargs):
        return bytes(nbytes)

    def writeto_mem(self, *args, **kwargs):
        pass


SoftI2C = I2C


class RTC:
    def __init__(self, *args, **kwargs):
        pass

    def datetime(self, dt=None):
        if dt is not None:
            return  # setting the host clock isn't supported; accept and ignore
        d = js.Date.new()
        return (
            d.getFullYear(), d.getMonth() + 1, d.getDate(),
            (d.getDay() + 6) % 7,               # Mon=0..Sun=6
            d.getHours(), d.getMinutes(), d.getSeconds(), 0,
        )

    def init(self, *args, **kwargs):
        pass


def reset():
    r = _host("sim_reset")
    if r is not None:
        r()


def soft_reset():
    pass


def unique_id():
    return b"\xba\xd9\xe0\x05\x1e\x00\x00\x01"


def freq(*args):
    return 200000000  # 200 MHz, matching the tufty2350 board


def idle(*args):
    pass


def lightsleep(*args):
    pass


def disable_irq():
    return 0


def enable_irq(state):
    pass
