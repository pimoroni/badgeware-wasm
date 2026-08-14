# Real-time clock shim. The board carries a PCF85063A over I2C; here the host clock is
# the only one there is, so the time is read off that and setting it is dropped.
#
# `datetime` returns seven fields and not the eight `time.localtime` gives: badgeware.rtc
# unpacks exactly seven, and hands the seventh back as the weekday.
#
# The alarm and the timer are accepted and never fire. Nothing drives the chip's interrupt
# line here, and a flag that came back set would have `rtc.timer_elapsed` report an alarm
# the app never asked for.

import time


class PCF85063A:
    def __init__(self, *args, **kwargs):
        self._alarm = None

    def datetime(self, dt=None):
        if dt is not None:
            return None                       # the host clock is not ours to set
        year, month, day, hour, minute, second, weekday = time.localtime()[:7]
        return (year, month, day, hour, minute, second, weekday)

    def set_timer(self, ticks, *args, **kwargs):
        pass

    def enable_timer_interrupt(self, enable=True):
        pass

    def read_timer_flag(self):
        return False

    def clear_timer_flag(self):
        pass

    def set_alarm(self, second=0, minute=0, hour=0):
        self._alarm = (second, minute, hour)

    def unset_alarm(self):
        self._alarm = None

    def enable_alarm_interrupt(self, enable=True):
        pass

    def read_alarm_flag(self):
        return False

    def clear_alarm_flag(self):
        pass
