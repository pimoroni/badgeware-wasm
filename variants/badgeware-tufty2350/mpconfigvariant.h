// Badgeware simulator for the Pimoroni Tufty 2350.
#define MICROPY_HW_BOARD_NAME                   "Pimoroni Tufty 2350"
#define MICROPY_HW_MCU_NAME                     "RP2350"

#define MICROPY_CONFIG_ROM_LEVEL                (MICROPY_CONFIG_ROM_LEVEL_FULL_FEATURES)

// Cooperative VM yield + auto split heap, matching the asyncify/jspi backends
// (the async backend's own mpconfigvariant.h isn't on the include path here, so
// these are set explicitly). Keeps a long-running or self-looping badge program
// responsive and its heap bounded.
#define MICROPY_ENABLE_VM_YIELD                 (1)
#define MICROPY_GC_SPLIT_HEAP                   (1)
#define MICROPY_GC_SPLIT_HEAP_AUTO              (1)
#define MICROPY_PY_WEAKREF                      (1)
#define MICROPY_TRACKED_ALLOC                   (1)

// picovector wires its std::vector / rasteriser onto the MicroPython GC heap and
// expects the allocated-size malloc ABI (see picovector.config.hpp). The whole
// build must agree, so enable it here rather than only on the picovector target.
#define MICROPY_MALLOC_USES_ALLOCATED_SIZE      (1)

// The pure-Python st7789 shim gets its framebuffer address via uctypes.addressof
// to blit it to the host canvas without copying.
#define MICROPY_PY_UCTYPES                      (1)

// No native code emitter on wasm, so accept @micropython.native (it would
// otherwise be a SyntaxError) and run the function as bytecode. @micropython.viper
// is deliberately left erroring.
#define MICROPY_EMIT_NATIVE_AS_BYTECODE         (1)
