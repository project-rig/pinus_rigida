# Import modules
import itertools
import logging
import numpy as np
from pyNN import recording

# Import classes
from bitarray import bitarray
from collections import defaultdict
from rig.utils.contexts import ContextMixin

from . import simulator

logger = logging.getLogger("pynn_spinnaker")


# ----------------------------------------------------------------------------
# Recorder
# ----------------------------------------------------------------------------
class Recorder(recording.Recorder, ContextMixin):
    _simulator = simulator

    def __init__(self, population, file=None):
        # Superclass
        super(Recorder, self).__init__(population, file)

        # Initialise the context stack
        ContextMixin.__init__(self, {})

        # Create default dictionary of population-size bitarrays
        self.indices_to_record = defaultdict(
            lambda: bitarray(itertools.repeat(0, population.size),
                             endian="little"))

    def _record(self, variable, new_ids, sampling_interval=None):
        # Get bitarray of indices to record for this variable
        indices = self.indices_to_record[variable]

        # Loop through the new ids
        for new_id in new_ids:
            # Convert to index
            new_index = self.population.id_to_index(new_id)

            # Set this bit in indices
            indices[new_index] = True

    def _read_vertex(self, n_cluster, vertex, variables_to_include,
                     spike_times, signals):
        # Loop through all variables to include
        for variable in variables_to_include:
            # If this variable is a spike recording, update the
            # spike times dictionary with spikes from this vertex
            if variable == "spikes":
                spike_times.update(n_cluster.read_spike_times(
                    vertex.region_memory, vertex.neuron_slice))
            # Otherwise
            else:
                # Convert variable name to channel number
                # **HACK** subtract one assuming first entry is spikes
                channel =\
                    self.population.celltype.recordable.index(variable) - 1

                # Update this variables dictionary with values from this vertex
                signals[variable].update(n_cluster.read_signal(
                    channel, vertex.region_memory, vertex.neuron_slice))

    def _get_current_segment(self, filter_ids=None,
                             variables='all', clear=False):
        logger.info("Downloading recorded data for population %s",
                    self.population.label)

        vars_to_include = set(self.recorded.keys())
        if variables is not "all":
            vars_to_include = vars_to_include.intersection(set(variables))

        # If a SpiNNaker neuron population was
        # created for the recorded population
        sim_state = self._simulator.state
        spike_times = {}
        signals = defaultdict(dict)
        if self.population in sim_state.pop_neuron_clusters:
            # Get neuron cluster
            n_cluster = sim_state.pop_neuron_clusters[self.population]

            # Loop through all neuron vertices and read
            for vertex in n_cluster.verts:
                self._read_vertex(n_cluster, vertex, vars_to_include,
                                  spike_times, signals)

        # Create context containing data read
        # from spinnaker and call superclass
        with self.get_new_context(spike_times=spike_times, signals=signals):
            return super(Recorder, self)._get_current_segment(filter_ids,
                                                              variables, clear)

    @ContextMixin.use_contextual_arguments()
    def _get_spiketimes(self, id, spike_times, signals):
        # Convert id to index
        index = self.population.id_to_index(id)

        # Return the numpy array of spike times associated with this index
        return spike_times[index]

    @ContextMixin.use_contextual_arguments()
    def _get_all_signals(self, variable, ids, spike_times,
                         signals, clear=False):
        # Stack together signals for this variable from all ids
        signal = signals[variable]
        return np.vstack((signal[self.population.id_to_index(id)]
                          for id in ids)).T

    def _localpass_count(self, variable, filter_ids=None):
        N = {}
        if variable == "spikes":
            raise NotImplementedError("Not implemented")
        else:
            raise Exception("Only implemented for spikes")
        return N

    def _clear_simulator(self):
        pass

    def _reset(self):
        pass
