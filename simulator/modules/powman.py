# Power management shim. The real module drives the RP2350's POWMAN block to sleep the
# board, wake it on a button, and reboot it into mass storage. A tab can do none of those,
# so sleeping returns at once and the wake reason is always the one for a plain reset.
#
# The constants are the firmware's: `badgeware.badge.woken_by_button` compares against
# them, and `woken_by_reset` against 255.

WAKE_BUTTON_A = 0
WAKE_BUTTON_B = 1
WAKE_BUTTON_C = 2
WAKE_BUTTON_UP = 3
WAKE_BUTTON_DOWN = 4
WAKE_WATCHDOG = 241
WAKE_UNKNOWN = 255


def get_wake_reason():
    return WAKE_UNKNOWN


def get_wake_buttons():
    return ()


def pressed_to_wake():
    return False


def sleep():
    pass


def goto_dormant_for(duration=None):
    pass


def reset_into_msc():
    fatal_error("Error!", "MSC not supported in the simulator.")  # noqa: F821
