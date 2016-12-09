Connection Builder
******************
The connection builder is used to generate synaptic matrices for the synapse
processor on SpiNNaker itself. To simplify this process it uses the same region
layout as the synapse processor allowing it to be run between
SDRAM data being loaded and the simulation executables being run.

Connector generators
====================

.. doxygennamespace:: ConnectionBuilder::ConnectorGenerator
  :content-only:

Parameter generators
====================
Parameter generators are used to generate both synaptic delays and weights.
Based on number of synapses in a row calculated by the connector generator,
parameter generators will return corresponding values in an
arbitrary fixed-point format.

.. doxygennamespace:: ConnectionBuilder::ParamGenerator
  :content-only: