# Location of top-level MicroPython directory
MPY_DIR = ../../../../micropython

# Name of module
MOD = ubmfont

# Source files (.c or .py)
SRC = m_unicode.c m_utils.c font_query.c font_draw.c ubmfont.c

# Architecture to build for (x86, x64, armv7m, xtensa, xtensawin)
ARCH = x64

CFLAGS += -Wno-unused-but-set-variable -Wno-unused-const-variable -Wno-unused-function -Wno-unused-variable

# Include to get the rules for compiling and linking the module
include $(MPY_DIR)/py/dynruntime.mk
