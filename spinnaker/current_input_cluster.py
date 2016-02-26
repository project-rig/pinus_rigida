# Import modules
import enum
import logging
import regions
from os import path
from rig import machine

# Import classes
from collections import defaultdict
from utils import (Args, InputVertex)

# Import functions
from six import iteritems
from utils import (create_app_ptr_and_region_files_named, split_slice,
                   model_binaries, sizeof_regions_named)

logger = logging.getLogger("pinus_rigida")


# ------------------------------------------------------------------------------
# Regions
# ------------------------------------------------------------------------------
class Regions(enum.IntEnum):
    """Region names, corresponding to those defined in `current_input.h`"""
    system = 0
    neuron = 1
    output_buffer = 2
    output_weight = 3
    spike_recording = 4
    profiler = 5


# ------------------------------------------------------------------------------
# CurrentInputCluster
# ------------------------------------------------------------------------------
class CurrentInputCluster(object):
    # Tag names, corresponding to those defined in current_input.h
    profiler_tag_names = {
        0:  "Timer tick",
    }

    def __init__(self, cell_type, parameters, initial_values, sim_timestep_ms,
                 timer_period_us, sim_ticks, indices_to_record, config,
                 receptor_index, vertex_applications, vertex_resources,
                 post_synaptic_width):
        # Create standard regions
        self.regions = {}
        self.regions[Regions.system] = regions.System(
            timer_period_us, sim_ticks)
        self.regions[Regions.neuron] = cell_type.neuron_region_class(
            cell_type, parameters, initial_values, sim_timestep_ms)
        self.regions[Regions.output_buffer] = regions.OutputBuffer()
        self.regions[Regions.output_weight] = regions.OutputWeight()
        self.regions[Regions.spike_recording] = regions.SpikeRecording(
            indices_to_record, sim_timestep_ms, sim_ticks)

        # Create start of filename for the executable to use for this cluster
        filename = "current_input_" + cell_type.__class__.__name__.lower()

        # Add profiler region if required
        if config.num_profile_samples is not None:
            self.regions[Regions.profiler] =\
                regions.Profiler(config.num_profile_samples)
            filename += "_profiled"

        # Slice current input
        post_slices = split_slice(parameters.shape[0], post_synaptic_width)

        current_input_app = path.join(model_binaries, filename + ".aplx")
        logger.debug("\t\t\tCurrent input application:%s",
                     current_input_app)

        # Loop through slice
        self.verts = []
        for post_slice in post_slices:
            logger.debug("\t\t\tPost slice:%s", str(post_slice))

            # Build input vert and add to list
            input_vert = InputVertex(post_slice, receptor_index)
            self.verts.append(input_vert)

            # Add application to dictionary
            vertex_applications[input_vert] = current_input_app

            # Add resources to dictionary
            # **TODO** add SDRAM
            vertex_resources[input_vert] = {machine.Cores: 1}

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def get_size(self, post_vertex_slice, weights, out_buffers):
        region_arguments = self._get_region_arguments(
            post_vertex_slice, weights, out_buffers)

        # Calculate region size
        vertex_size_bytes = sizeof_regions_named(self.regions,
                                                 region_arguments)

        logger.debug("\t\t\tRegion size = %u bytes", vertex_size_bytes)
        return vertex_size_bytes

    def write_to_file(self, post_vertex_slice, weights, out_buffers, fp):
        region_arguments = self._get_region_arguments(
            post_vertex_slice, weights, out_buffers)

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

    def read_profile(self):
        # Get the profile recording region and
        region = self.regions[Regions.profiler]

        # Return profile data for each vertex that makes up population
        return [(v.post_neuron_slice.python_slice,
                 region.read_profile(v.region_memory[Regions.profiler],
                                     self.profiler_tag_names))
                for v in self.verts]

    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _get_region_arguments(self, post_vertex_slice, weights, out_buffers):
        region_arguments = defaultdict(Args)

        # Add vertex slice to regions that require it
        for r in (Regions.neuron,
                  Regions.output_weight,
                  Regions.spike_recording):
            region_arguments[r] = Args(post_vertex_slice)

        # Add kwargs for regions that require them
        region_arguments[Regions.system].kwargs["application_words"] =\
            [len(post_vertex_slice)]

        region_arguments[Regions.output_buffer].kwargs["out_buffers"] =\
            out_buffers

        region_arguments[Regions.output_weight].kwargs["weights"] = weights

        return region_arguments
