Connection Builder
******************
The connection builder is used to generate synaptic matrices for the synapse
processor on SpiNNaker itself. To simplify this process it uses the same region
layout as the synapse processor allowing it to be run between
SDRAM data being loaded and the simulation executables being run.

When loaded, the connection builder reads in the region generated in Python by
:py:class:`~pynn_spinnaker.spinnaker.regions.ConnectionBuilder`. For each
sub-matrix to be generated on chip it then uses the
:cpp:class:`~ConnectionBuilder::GeneratorFactory` to create a suitable
:cpp:class:`ConnectionBuilder::MatrixGenerator::Base`-derived object to create
the correct synaptic matrix structure, a suitable
:cpp:class:`ConnectionBuilder::ConnectorGenerator::Base`-derived object to
generate an array of postsynaptic indices for each synaptic matrix row; and
:cpp:class:`ConnectionBuilder::ParamGenerator::Base`-derived objects to generate
the delays and weights for each synapse.

Generator factory
=================

.. doxygenclass:: ConnectionBuilder::GeneratorFactory
  :members:

Matrix generators
=================

.. doxygennamespace:: ConnectionBuilder::MatrixGenerator
  :members:
  :protected-members:


Connector generators
====================

.. doxygennamespace:: ConnectionBuilder::ConnectorGenerator
  :members:

Parameter generators
====================
Parameter generators are used to generate both synaptic delays and weights.
Based on number of synapses in a row calculated by the connector generator,
parameter generators will return corresponding values in an
arbitrary fixed-point format.

.. doxygennamespace:: ConnectionBuilder::ParamGenerator
  :members: