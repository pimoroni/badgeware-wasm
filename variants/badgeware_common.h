// Shared MicroPython feature config for the badgeware simulator variants. Each
// board's mpconfigvariant.h defines MICROPY_HW_BOARD_NAME / _MCU_NAME and then
// includes this.

#define MICROPY_CONFIG_ROM_LEVEL                (MICROPY_CONFIG_ROM_LEVEL_FULL_FEATURES)

// Cooperative VM yield + auto split heap, matching the asyncify/jspi backends
// (the async backend's own mpconfigvariant.h isn't on the include path here).
// Keeps a long-running or self-looping badge program responsive and its heap
// bounded.
#define MICROPY_ENABLE_VM_YIELD                 (1)
#define MICROPY_GC_SPLIT_HEAP                   (1)
#define MICROPY_GC_SPLIT_HEAP_AUTO              (1)
#define MICROPY_PY_WEAKREF                      (1)
#define MICROPY_TRACKED_ALLOC                   (1)

// picovector wires its std::vector / rasteriser onto the MicroPython GC heap and
// expects the allocated-size malloc ABI (see picovector.config.hpp). The whole
// build must agree, so enable it here rather than only on the picovector target.
#define MICROPY_MALLOC_USES_ALLOCATED_SIZE      (1)

// The pure-Python display shims get their framebuffer address via
// uctypes.addressof to blit it to the host canvas without copying.
#define MICROPY_PY_UCTYPES                      (1)

// The badgeware firmware identifies the board from os.uname().machine, e.g.
//   MODEL = os.uname().machine[9:-17].lower()   # "Pimoroni Tufty 2350 with RP2350" -> "tufty"
// so expose os.uname() (its machine field is MICROPY_HW_BOARD_NAME " with "
// MICROPY_HW_MCU_NAME). machine.unique_id() is provided by the machine shim.
#define MICROPY_PY_OS_UNAME                     (1)

// No native code emitter on wasm, so accept @micropython.native (it would
// otherwise be a SyntaxError) and run the function as bytecode. @micropython.viper
// is deliberately left erroring.
#define MICROPY_EMIT_NATIVE_AS_BYTECODE         (1)
