# Shared frozen modules for the badgeware simulator variants: the base port
# manifest (asyncio), the standard-library modules the badgeware library and its
# apps rely on, the machine / input simulation, and the fetch-backed networking
# shims. Each board's manifest.py includes this and adds its own display driver.

include("$(PORT_DIR)/variants/manifest.py")

# Python standard library (from micropython-lib).
require("abc")
require("base64")
require("collections")
require("collections-defaultdict")
require("copy")
require("datetime")
require("fnmatch")
require("functools")
require("gzip")
require("hmac")
require("html")
require("inspect")
require("io")
require("itertools")
require("locale")
require("logging")
require("operator")
require("os")
require("os-path")
require("pathlib")
require("stat")
require("tarfile")
require("tarfile-write")
require("time")
require("unittest")
require("uu")
require("zlib")

_SIM = "$(BADGEWARE_DIR)/simulator/modules"

# Simulated machine peripherals (Pin/PWM/ADC/I2C/RTC) and button input.
module("machine.py", base_path=_SIM, opt=3)
module("picovector_io.py", base_path=_SIM, opt=3)

# Networking. A browser can't open raw sockets, so the socket-based `requests`
# and `urllib.urequest` from micropython-lib can't run here; freeze fetch-backed
# shims (backed by the _jsfetch C module) under the usual names. `umqtt.simple`
# is raw-TCP with no fetch equivalent, frozen for source compatibility only.
module("requests.py", base_path=_SIM, opt=3)
package("urllib", ("urequest.py",), base_path=_SIM, opt=3)
require("umqtt.simple")

# AsyncFetch: a cooperative, streaming HTTP client shimmed onto the Fetch API.
module("fetch.py", base_path=_SIM, opt=3)

# Common firmware modules. easing, pimoroni and board are unchanged from the
# firmware; wifi is a simulator shim (no real WLAN - reports connected, since
# the browser network is reachable via fetch).
module("easing.py", base_path=_SIM, opt=3)
module("pimoroni.py", base_path=_SIM, opt=3)
module("board.py", base_path=_SIM, opt=3)
module("wifi.py", base_path=_SIM, opt=3)
# secrets loader: reads /secrets, falling back to the bundled default.
module("secrets.py", base_path=_SIM, opt=3)
# ntptime shim: no UDP/socket; reads the host clock instead.
module("ntptime.py", base_path=_SIM, opt=3)
