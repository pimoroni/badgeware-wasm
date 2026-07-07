# Frozen manifest for the badgeware-badger2350 simulator variant.
include("$(BADGEWARE_DIR)/simulator/manifest_common.py")

# Display: 264x176 SSD1680 e-ink (ssd1680.SSD1680).
module("ssd1680.py", base_path="$(BADGEWARE_DIR)/simulator/modules", opt=3)
