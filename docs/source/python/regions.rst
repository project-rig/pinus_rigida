Regions
*******
All executables divide data written to SpiNNakers SDRAM into 'regions' and on
the host-side, the :py:class:`~pynn_spinnaker.spinnaker.neural_cluster.NeuralCluster`,
a :py:class:`~pynn_spinnaker.spinnaker.neural_cluster.SynapseCluster` and
a :py:class:`~pynn_spinnaker.spinnaker.neural_cluster.CurrentInputCluster`
used to configure these objects are also composed of regions.

.. automodule:: pynn_spinnaker.spinnaker.regions
  :members: AnalogueRecording
  :undoc-members: