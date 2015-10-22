# SpiNNaker Nengo Integration
# ----------------------------------------------------------------------------
# Authors:
#  Andrew Mundy <mundya@cs.man.ac.uk>
#  Terry Stewart
#
# February - April 2014
# ----------------------------------------------------------------------------
# Code derived from Andrew Rowley, University of Manchester

APPS = neuron_processor synapse_processor

all :
	for a in $(APPS); do ( cd $$a; "$(MAKE)"  ) || exit $$?; done

clean :
	for a in $(APPS); do ( cd $$a; "$(MAKE)" clean  ) || exit $$?; done
