# Import modules
import enum
import itertools
import logging
import regions
from os import path
from rig import machine

# Import classes
from collections import defaultdict
from utils import Args

# Import functions
from six import iteritems
from utils import (create_app_ptr_and_region_files_named, split_slice,
                   model_binaries, sizeof_regions_named)

logger = logging.getLogger("pinus_rigida")


# -----------------------------------------------------------------------------
# Regions
# -----------------------------------------------------------------------------
class Regions(enum.IntEnum):
    # JK: probably update this and try and use relative enum numbering
    """Region names, corresponding to those defined in `ensemble.h`"""
    system = 0
    neuron = 1
    synapse = 2
    input_buffer = 3
    spike_recording = 4
    analogue_recording_start = 5
    analogue_recording_end = analogue_recording_start + 4
    profiler = analogue_recording_end

#------------------------------------------------------------------------------
# Vertex
#------------------------------------------------------------------------------
class Vertex(object):
    def __init__(self, parent_keyspace, neuron_slice, population_index, vertex_index):
        self.neuron_slice = neuron_slice
        self.keyspace = parent_keyspace(population_index=population_index,
            vertex_index=vertex_index)
        self.input_verts = list()
        self.region_memory = None

    @property
    def key(self):
        return self.keyspace.get_value(tag="routing")

    @property
    def mask(self):
        return self.keyspace.get_mask(tag="routing")

    def __str__(self):
        return "<neuron slice:%s>" % (str(self.neuron_slice))

# -----------------------------------------------------------------------------
# NeuralCluster
# -----------------------------------------------------------------------------
class NeuralCluster(object):
    # Tag names, corresponding to those defined in neuron_processor.h
    profiler_tag_names = {
        0:  "Synapse shape",
        1:  "Update neurons",
        2:  "Apply buffer",
    }

    def __init__(self, pop_id, cell_type, parameters, initial_values,
                 sim_timestep_ms, timer_period_us, sim_ticks,
                 indices_to_record, config, vertex_applications,
                 vertex_resources, keyspace):
        # Create standard regions
        self.regions = {}
        self.regions[Regions.system] = regions.System(
            timer_period_us, sim_ticks)
        self.regions[Regions.neuron] = cell_type.neuron_region_class(
            cell_type, parameters, initial_values, sim_timestep_ms)
        self.regions[Regions.spike_recording] = regions.SpikeRecording(
            indices_to_record, sim_timestep_ms, sim_ticks)

        # If cell type has any receptors i.e. any need for synaptic input
        if len(cell_type.receptor_types) > 0:
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

        # Create start of filename for the executable to use for this cluster
        filename = "neuron_" + cell_type.__class__.__name__.lower()

        # Add profiler region if required
        # JH, AM, JK: Agreed this system doesn't make sense in PyNN as we have objects
        if config.get("profile_samples", None) is not None:
            self.regions[Regions.profiler] =\
                regions.Profiler(config["profile_samples"])
            filename += "_profiled"

        # Split population slice
        # **TODO** pick based on timestep and parameters
        neuron_slices = split_slice(parameters.shape[0],
                                    cell_type.max_neurons_per_core)

        # Build neuron vertices for each slice allocating a keyspace for each vertex
        self.verts = [Vertex(keyspace, neuron_slice, pop_id, vert_id)
                      for vert_id, neuron_slice in enumerate(neuron_slices)]

        # Get neuron application name
        neuron_app = path.join(model_binaries, filename + ".aplx")

        logger.debug("\t\tNeuron application:%s", neuron_app)
        logger.debug("\t\t%u neuron vertices", len(self.verts))

        # Loop through neuron vertices and their corresponding resources
        for v in self.verts:
            # Add application to dictionary
            vertex_applications[v] = neuron_app

            # Add resources to dictionary
            # **TODO** add SDRAM
            vertex_resources[v] = { machine.Cores: 1 }

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def get_size(self, key, vertex_slice, in_buffers):
        region_arguments = self._get_region_arguments(key, vertex_slice,
                                                      in_buffers)

        # Calculate region size
        vertex_size_bytes = sizeof_regions_named(self.regions,
                                                 region_arguments)

        logger.debug("\t\t\tRegion size = %u bytes", vertex_size_bytes)
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
        # Get index of channelread_profile
        r = Regions(Regions.analogue_recording_start + channel)

        # Get the analogue recording region and
        # the memory block associated with it
        # Use analogue recording region to get signal
        return self.regions[r].read_signal(vertex_slice, region_memory[r])

    def read_profile(self):
        # Get the profile recording region and
        region = self.regions[Regions.profiler]

        # Return profile data for each vertex that makes up population
        return [(v.neuron_slice.python_slice,
                 region.read_profile(v.region_memory[Regions.profiler],
                                     self.profiler_tag_names))
                 for v in self.verts]

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
            region_arguments[r] = Args(vertex_slice)

        # Add kwargs for regions that require them
        region_arguments[Regions.system].kwargs["application_words"] =\
            [key, len(vertex_slice)]
        region_arguments[Regions.input_buffer].kwargs["in_buffers"] =\
            in_buffers

        return region_arguments
