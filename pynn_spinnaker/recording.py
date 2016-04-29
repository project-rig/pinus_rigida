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

    def _record(self, variable, new_ids, sampling_interval):
        # Get bitarray of indices to record for this variable
        indices = self.indices_to_record[variable]

        # **YUCK** update sampling interval if one is specified
        # (no idea why this has to be done in derived class)
        if sampling_interval is not None:
            self.sampling_interval = sampling_interval

        # Loop through the new ids
        for new_id in new_ids:
            # Convert to index
            new_index = self.population.id_to_index(new_id)

            # Set this bit in indices
            indices[new_index] = True

    def _get_current_segment(self, filter_ids=None,
                             variables='all', clear=False):
        logger.info("Downloading recorded data for population %s",
                    self.population.label)

        vars_to_read = set(self.recorded.keys())
        if variables is not "all":
            vars_to_read = vars_to_read.intersection(set(variables))

        # Read desired spike times and signals from population
        spike_times, signals = self.population._read_recorded_vars(vars_to_read)

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
