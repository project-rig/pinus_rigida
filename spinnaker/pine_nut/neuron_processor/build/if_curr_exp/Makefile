APP = if_curr_exp

# Extra objects for synapse and row-lookup type
EXTRA_SOURCES = ../../neuron_models/if_curr.cpp \
		../../synapse_models/exp.cpp

# Build object list
SOURCES = ../../../common/config.cpp \
	../../../common/bit_field.cpp \
	../../neuron_processor.cpp \
	$(EXTRA_SOURCES)

CFLAGS += -I $(CURDIR)

include ../../../Makefile.depend