Python components of PyNN SpiNNaker
***********************************
PyNN populations :py:class:`~pynn_spinnaker.Population` are first divided into
a :py:class:`~pynn_spinnaker.spinnaker.neural_cluster.NeuralCluster` representing
the neurons which make up the population and a
:py:class:`~pynn_spinnaker.spinnaker.synapse_cluster.SynapseCluster` for each
*type* of synapse arriving at the population.

Additionally if a :py:class:`~pynn_spinnaker.Population` has any incoming
:py:class:`~pynn_spinnaker.Projection` which meet the criteria tested in
:py:func:`~pynn_spinnaker.Projection._directly_connectable` -- essentially that
the connector is one-to-one and the presynaptic population is some sort of
spike source -- the :py:class:`~pynn_spinnaker.Projection` and
:py:class:`~pynn_spinnaker.Population` are replaced by a
:py:class:`~pynn_spinnaker.spinnaker.current_input_cluster.CurrentInputCluster`
which injects the input provided by the spike source directly into the
:py:class:`~pynn_spinnaker.spinnaker.neural_cluster.NeuralCluster` via SDRAM
buffers.

Reference manual
================
PyNN implementation
-------------------
.. toctree::
        :maxdepth: 2

        connector
        population
        projection
        random

SpiNNaker implementation
------------------------
.. toctree::
        :maxdepth: 2

        neural_cluster
        synapse_cluster
        current_input_cluster
        regions
        utils