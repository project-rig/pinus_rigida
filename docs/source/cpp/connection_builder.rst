Connection Builder
******************
The connection builder is used to generate synaptic matrices for the synapse
processor on SpiNNaker itself. To simplify this process it uses the same region
layout as the synapse processor allowing it to be run between
SDRAM data being loaded and the simulation executables being run.

sss
==================================================================
.. doxygenclass:: ConnectionBuilder::ParamGenerator::Base
  :members: