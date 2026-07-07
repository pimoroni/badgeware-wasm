# Frozen manifest for the badgeware-blinky2350 simulator variant.
include("$(BADGEWARE_DIR)/simulator/manifest_common.py")

# Display: 39x26 RGB LED matrix (blinky.Blinky).
module("blinky.py", base_path="$(BADGEWARE_DIR)/simulator/modules", opt=3)
