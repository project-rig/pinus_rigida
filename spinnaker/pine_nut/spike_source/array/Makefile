APP = spike_source_array
APP_OUTPUT_DIR = ../../../../model_binaries/
BUILD_DIR = build/

COMMON_DIR = ../../common

# Build object list
OBJECTS = $(COMMON_DIR)/config.o \
	spike_source_array.o \
	../common/spike_source.o

# Configure compiler options
LIBRARIES = -lspin1_api
CFLAGS += -Wall -Wextra -Ofast

include $(SPINN_DIRS)/Makefile.common

all: $(APP_OUTPUT_DIR)$(APP).aplx

clean:
	$(RM) $(OBJECTS) $(BUILD_DIR)$(APP).elf $(BUILD_DIR)$(APP).txt $(APP_OUTPUT_DIR)$(APP).aplx
