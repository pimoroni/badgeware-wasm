# Frozen manifest for the badgeware-tufty2350 simulator variant.
include("$(BADGEWARE_DIR)/simulator/manifest_common.py")

# Display: 320x240 ST7789 LCD (st7789.ST7789).
module("st7789.py", base_path="$(BADGEWARE_DIR)/simulator/modules", opt=3)
