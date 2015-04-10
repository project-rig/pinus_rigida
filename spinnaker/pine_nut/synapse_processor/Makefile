APP = synapse_processor
APP_OUTPUT_DIR = ../../../model_binaries/
BUILD_DIR = build

COMMON_DIR = ../common

# Synapse and row-lookup type
# **TODO** move into target makefiles
SYNAPSE_TYPE = static
ROW_LOOKUP_TYPE = linear

# Extra objects for synapse and row-lookup type
# **TODO** move into target makefiles
SYNAPSE_OBJECTS = synapse_static.o
ROW_LOOKUP_OBJECTS = row_lookup_linear.o

# Build object list
OBJECTS = $(COMMON_DIR)/config.o \
	$(COMMON_DIR)/spikes.o \
	ring_buffer.o \
	synapse_processor.o \
	$(SYNAPSE_OBJECTS) \
	$(ROW_LOOKUP_OBJECTS)

# Configure compiler options
LIBRARIES = -lspin1_api
CFLAGS += -Wall -Wextra -Ofast 

include $(SPINN_DIRS)/Makefile.common

all: $(APP_OUTPUT_DIR)$(APP).aplx

clean:
	$(RM) $(OBJECTS) $(BUILD_DIR)$(APP).elf $(BUILD_DIR)$(APP).txt $(APP_OUTPUT_DIR)$(APP).aplx
