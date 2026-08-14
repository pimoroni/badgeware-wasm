# Frozen manifest for the badgeware-tufty2350-batteries variant: the tufty2350 manifest,
# plus the badgeware runtime and the two peripheral shims it imports.
include("$(BADGEWARE_DIR)/simulator/manifest_common.py")

# Display: 320x240 ST7789 LCD (st7789.ST7789).
module("st7789.py", base_path="$(BADGEWARE_DIR)/simulator/modules", opt=3)

# The firmware's own runtime, from a checkout of it rather than a copy kept here: this is
# what injects `badge`, `screen`, `image`, `tween` and the buttons into builtins, and a
# copy would drift from the badge it stands for.
package("badgeware", base_path="$(FIRMWARE_DIR)/modules/common", opt=3)

# What that package imports and the simulator has no hardware for. Frozen only in this
# variant: the ordinary build leaves them on the filesystem beside the runtime.
_SIM = "$(BADGEWARE_DIR)/simulator/modules"
module("powman.py", base_path=_SIM, opt=3)
module("pcf85063a.py", base_path=_SIM, opt=3)
