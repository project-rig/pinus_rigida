# Import modules
import enum
import itertools
import logging
import regions

# Import classes
from collections import defaultdict

# Import functions
from six import iteritems
from utils import (
    Args, create_app_ptr_and_region_files_named, sizeof_regions_named)

logger = logging.getLogger("pinus_rigida")


# -----------------------------------------------------------------------------
# Regions
# -----------------------------------------------------------------------------
class Regions(enum.IntEnum):
    """Region names, corresponding to those defined in `ensemble.h`"""
    system = 0,
    neuron = 1,
    synapse = 2,
    input_buffer = 3,
    spike_recording = 4,
    analogue_recording_start = 5,
    analogue_recording_0 = 5,
    analogue_recording_1 = 6,
    analogue_recording_2 = 7,
    analogue_recording_3 = 8,
    analogue_recording_end = 9,
    profiler = 9,


# -----------------------------------------------------------------------------
# NeuralPopulation
# -----------------------------------------------------------------------------
class NeuralPopulation(object):
    def __init__(self, cell_type, parameters, initial_values,
                 sim_timestep_ms, timer_period_us, sim_ticks,
                 indices_to_record):
        # Create standard regions
        self.regions = {}
        self.regions[Regions.system] = regions.System(
            timer_period_us, sim_ticks)
        self.regions[Regions.neuron] = cell_type.neuron_region_class(
            cell_type, parameters, initial_values, sim_timestep_ms)
        self.regions[Regions.spike_recording] = regions.SpikeRecording(
            indices_to_record, sim_timestep_ms, sim_ticks)

        # If cell type has a synapse region class
        if hasattr(cell_type, "synapse_region_class"):
            # Add a synapse region and an input buffer
            self.regions[Regions.synapse] = cell_type.synapse_region_class(
                cell_type, parameters, initial_values, sim_timestep_ms)

            self.regions[Regions.input_buffer] = regions.InputBuffer()

        # Assert that there are sufficient analogue
        # recording regions for this celltype's needs
        assert (Regions.analogue_recording_end -
                Regions.analogue_recording_start) >=\
                    (len(cell_type.recordable) - 1)

        # Loop through cell's non-spike recordables
        # and create analogue recording regions
        # **HACK** this assumes the first entry is spike
        for i, v in enumerate(cell_type.recordable[1:]):
            self.regions[Regions(Regions.analogue_recording_start + i)] =\
                regions.AnalogueRecording(indices_to_record, v,
                                          sim_timestep_ms, sim_ticks)

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def get_size(self, key, vertex_slice, in_buffers):
        region_arguments = self._get_region_arguments(key, vertex_slice,
                                                      in_buffers)

        # Calculate region size
        vertex_size_bytes = sizeof_regions_named(self.regions,
                                                 region_arguments)

        logger.debug("\t\t\tRegion size = %u bytes" % vertex_size_bytes)
        return vertex_size_bytes

    def write_to_file(self, key, vertex_slice, in_buffers, fp):
        region_arguments = self._get_region_arguments(key, vertex_slice,
                                                      in_buffers)

        # Layout the slice of SDRAM we have been given
        region_memory = create_app_ptr_and_region_files_named(
            fp, self.regions, region_arguments)

        # Write each region into memory
        for key, region in iteritems(self.regions):
            # Get memory
            mem = region_memory[key]

            # Get the arguments
            args, kwargs = region_arguments[key]

            # Perform the write
            region.write_subregion_to_file(mem, *args, **kwargs)
        return region_memory

    def read_spike_times(self, region_memory, vertex_slice):
        # Get the spike recording region and
        # the memory block associated with it
        region = self.regions[Regions.spike_recording]

        # Use spike recording region to get spike times
        return region.read_spike_times(vertex_slice,
                                       region_memory[Regions.spike_recording])

    def read_signal(self, channel, region_memory, vertex_slice):
        # Get index of channel
        r = Regions(Regions.analogue_recording_start + channel)

        # Get the analogue recording region and
        # the memory block associated with it
        # Use analogue recording region to get signal
        return self.regions[r].read_signal(vertex_slice, region_memory[r])

    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _get_region_arguments(self, key, vertex_slice, in_buffers):
        region_arguments = defaultdict(Args)

        analogue_recording_regions = range(Regions.analogue_recording_start,
                                           Regions.analogue_recording_end)
        # Add vertex slice to regions that require it
        for r in itertools.chain((Regions.neuron,
                                  Regions.synapse,
                                  Regions.spike_recording),
                                 analogue_recording_regions):
            region_arguments[Regions(r)] = Args(vertex_slice)

        # Add kwargs for regions that require them
        region_arguments[Regions.system].kwargs["application_words"] =\
            [key, vertex_slice.slice_length]
        region_arguments[Regions.input_buffer].kwargs["in_buffers"] =\
            in_buffers

        return region_arguments
