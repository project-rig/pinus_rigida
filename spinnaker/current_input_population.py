# Import modules
import enum
import logging
import regions

# Import classes
from collections import defaultdict

# Import functions
from six import iteritems
from utils import (
    Args, create_app_ptr_and_region_files_named, sizeof_regions_named)

logger = logging.getLogger("pinus_rigida")

# ------------------------------------------------------------------------------
# Regions
# ------------------------------------------------------------------------------
class Regions(enum.IntEnum):
    """Region names, corresponding to those defined in `ensemble.h`"""
    system = 0,
    neuron = 1,
    output_buffer = 2,
    output_weight = 3
    spike_recording = 4,
    profiler = 5,


# ------------------------------------------------------------------------------
# CurrentInputPopulation
# ------------------------------------------------------------------------------
class CurrentInputPopulation(object):
    def __init__(self, cell_type, parameters, initial_values, sim_timestep_ms,
                 timer_period_us, sim_ticks, indices_to_record, config,
                 weights):
        # Create standard regions
        self.regions = {}
        self.regions[Regions.system] = regions.System(
            timer_period_us, sim_ticks)
        self.regions[Regions.neuron] = cell_type.neuron_region_class(
            cell_type, parameters, initial_values, sim_timestep_ms)
        self.regions[Regions.output_buffer] = regions.OutputBuffer()
        self.regions[Regions.output_weight] = regions.OutputWeight(weights)
        self.regions[Regions.spike_recording] = regions.SpikeRecording(
            indices_to_record, sim_timestep_ms, sim_ticks)

        # Add profiler region if required
        if config.get("profile_samples", None) is not None:
            self.regions[Regions.profiler] = regions.Profiler(config["profile_samples"])


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def get_size(self, post_vertex_slice, out_buffers):
        region_arguments = self._get_region_arguments(
            post_vertex_slice, out_buffers)

        # Calculate region size
        vertex_size_bytes = sizeof_regions_named(self.regions,
                                                 region_arguments)

        logger.debug("\t\t\tRegion size = %u bytes" % vertex_size_bytes)
        return vertex_size_bytes

    def write_to_file(self, post_vertex_slice, out_buffers, fp):
        region_arguments = self._get_region_arguments(
            post_vertex_slice, out_buffers)

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
    
    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _get_region_arguments(self, post_vertex_slice, out_buffers):
        region_arguments = defaultdict(Args)

        # Add vertex slice to regions that require it
        for r in (Regions.neuron,
                  Regions.output_weight,
                  Regions.spike_recording):
            region_arguments[Regions(r)] = Args(post_vertex_slice)

        # Add kwargs for regions that require them
        region_arguments[Regions.system].kwargs["application_words"] =\
            [post_vertex_slice.slice_length]

        region_arguments[Regions.output_buffer].kwargs["out_buffers"] =\
            out_buffers

        return region_arguments
