Python components of PyNN SpiNNaker
***********************************
PyNN populations :py:class:`~pynn_spinnaker.Population` are first divided into
a :py:class:`~pynn_spinnaker.spinnaker.neural_cluster.NeuralCluster` representing
the neurons which make up the population and a
:py:class:`~pynn_spinnaker.spinnaker.synapse_cluster.SynapseCluster` for each
*type* of .
*
Additionally if there are any incoming :py:class:`~pynn_spinnaker.Population`
which meet the criteria tested in :py:func:`~pynn_spinnaker.Projection._directly_connectable`

Reference manual
================
PyNN implementation
-------------------
.. toctree::
        :maxdepth: 2

        population
        projection

SpiNNaker implementation
------------------------
.. toctree::
        :maxdepth: 2

        neural_cluster
        synapse_cluster
        current_input_cluster
        regions
        utils