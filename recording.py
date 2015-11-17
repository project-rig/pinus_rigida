# Import modules
import itertools
import numpy
from pyNN import recording

# Import classes
from bitarray import bitarray
from collections import defaultdict

from . import simulator


class Recorder(recording.Recorder):
    _simulator = simulator

    def __init__(self, population, file=None):
        # Superclass
        super(Recorder, self).__init__(population, file)

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

    def _get_spiketimes(self, id):
        return numpy.array([id, id+5], dtype=float) % self._simulator.state.t

    def _get_all_signals(self, variable, ids, clear=False):
        # assuming not using cvode, otherwise need to get times as well and use IrregularlySampledAnalogSignal
        n_samples = int(round(self._simulator.state.t/self._simulator.state.dt)) + 1
        return numpy.vstack((numpy.random.uniform(size=n_samples) for id in ids)).T

    def _local_count(self, variable, filter_ids=None):
        N = {}
        if variable == 'spikes':
            for id in self.filter_recorded(variable, filter_ids):
                N[int(id)] = 2
        else:
            raise Exception("Only implemented for spikes")
        return N

    def _clear_simulator(self):
        pass

    def _reset(self):
        pass
