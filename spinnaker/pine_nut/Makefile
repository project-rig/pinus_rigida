# SpiNNaker Nengo Integration
# ----------------------------------------------------------------------------
# Authors:
#  Andrew Mundy <mundya@cs.man.ac.uk>
#  Terry Stewart
#
# February - April 2014
# ----------------------------------------------------------------------------
# Code derived from Andrew Rowley, University of Manchester

APPS = neuron_processor synapse_processor spike_source_poisson current_input_poisson

all :
	for a in $(APPS); do ( cd $$a; "$(MAKE)" PROFILER_ENABLED=1 ) || exit $$?; done
	for a in $(APPS); do ( cd $$a; "$(MAKE)" PROFILER_ENABLED=1 ) || exit $$?; done

clean :
	for a in $(APPS); do ( cd $$a; "$(MAKE)" clean PROFILER_ENABLED=1 ) || exit $$?; done
	for a in $(APPS); do ( cd $$a; "$(MAKE)" clean PROFILER_ENABLED=1 ) || exit $$?; done
