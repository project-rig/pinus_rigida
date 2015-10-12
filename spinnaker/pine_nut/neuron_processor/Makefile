APP = synapse_processor

# **TODO** move into target makefiles
CONFIG_HEADER = config/lif_curr_exp.h

# Extra objects for synapse and row-lookup type
EXTRA_SOURCES = neuron_models/lif_curr.cpp

# Build object list
SOURCES = ../common/config.cpp \
	neuron_processor.cpp \
	$(EXTRA_SOURCES)

include ../Makefile.depend