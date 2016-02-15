# Import modules
import enum
import logging
import regions
from os import path
from rig import machine

# Import classes
from collections import defaultdict
from utils import Args, InputVertex

# Import functions
from six import iteritems
from utils import (create_app_ptr_and_region_files_named, evenly_slice,
                   model_binaries, sizeof_regions_named)

logger = logging.getLogger("pinus_rigida")

# ------------------------------------------------------------------------------
# Regions
# ------------------------------------------------------------------------------
class Regions(enum.IntEnum):
    """Region names, corresponding to those defined in `ensemble.h`"""
    system = 0
    key_lookup = 1
    synaptic_matrix = 2
    plasticity = 3
    output_buffer = 4
    profiler = 5

#------------------------------------------------------------------------------
# Vertex
#------------------------------------------------------------------------------
class Vertex(InputVertex):
    def __init__(self, post_neuron_slice, receptor_index):
        # Superclass
        super(Vertex, self).__init__(post_neuron_slice, receptor_index)

        self.incoming_connections = defaultdict(list)

    def add_connection(self, pre_pop, pre_neuron_vertex):
        self.incoming_connections[pre_pop].append(pre_neuron_vertex)

# ------------------------------------------------------------------------------
# SynapseCluster
# ------------------------------------------------------------------------------
class SynapseCluster(object):
    # Tag names, corresponding to those defined in synapse_processor.h
    profiler_tag_names = {
        0:  "Timer tick",
        1:  "Multicast packet received",
        2:  "Setup next DMA row read",
        3:  "Process row",
    }

    def __init__(self, timer_period_us, sim_ticks, config, post_pop_size,
                 synapse_model, receptor_index, synaptic_projections,
                 pop_neuron_clusters, vertex_applications, vertex_resources):
        # Dictionary of regions
        self.regions = {}
        self.regions[Regions.system] = regions.System(timer_period_us,
                                                      sim_ticks)
        self.regions[Regions.key_lookup] = regions.KeyLookupBinarySearch()
        self.regions[Regions.synaptic_matrix] = regions.SynapticMatrix()
        self.regions[Regions.output_buffer] = regions.OutputBuffer()

        # Create start of filename for the executable to use for this cluster
        filename = "synapse_" + synapse_model.__name__.lower()

        # Add profiler region if required
        if config.get("profile_samples", None) is not None:
            self.regions[Regions.profiler] = regions.Profiler(config["profile_samples"])
            filename += "_profiled"

        # Slice post-synaptic neurons evenly based on synapse type
        # **NOTE** this is typically based only on memory
        post_slices = evenly_slice(
            post_pop_size, synapse_model.max_post_neurons_per_core)

        logger.debug("\t\tSynapse model:%s, Receptor index:%u",
            synapse_model, receptor_index)

        # Get synapse application name
        # **THINK** is there any point in doing anything cleverer than this
        synapse_app = path.join(model_binaries, filename + ".aplx")
        logger.debug("\t\t\tSynapse application:%s", synapse_app)

        # Loop through the post-slices
        self.verts = []
        for post_slice in post_slices:
            logger.debug("\t\t\tPost slice:%s", str(post_slice))

            # Loop through all non-directly connectable projections of this type
            vertex_event_rate = 0.0
            vertex = Vertex(post_slice, receptor_index)
            for proj in synaptic_projections:
                # **TODO** check if projection and pre-population can be directly attached
                # Loop through the vertices which the pre-synaptic
                # population has been partitioned into
                for pre_vertex in pop_neuron_clusters[proj.pre].verts:
                    logger.debug("\t\t\t\tPre slice:%s", str(pre_vertex.neuron_slice))

                    # Estimate number of synapses the connection between
                    # The pre and the post-slice of neurons will contain
                    total_synapses = proj._estimate_num_synapses(
                        pre_vertex.neuron_slice, post_slice)

                    # Use this to calculate event rate
                    synaptic_event_rate = total_synapses * proj.pre._mean_firing_rate

                    # **TODO** SDRAM estimation
                    logger.debug("\t\t\t\t\tTotal synapses:%d, synaptic event rate:%f",
                                 total_synapses, synaptic_event_rate)

                    # Add this connection to the synapse vertex
                    vertex.add_connection(proj.pre, pre_vertex)

                    # Add event rate to total for current synapse processor
                    vertex_event_rate += synaptic_event_rate

                    # If it's more than this type of synapse processor can handle
                    if vertex_event_rate > synapse_model.max_synaptic_event_rate:
                        # Add current synapse vertex to list
                        self.verts.append(vertex)

                        # Create replacement and reset event rate
                        vertex = Vertex(post_slice, receptor_index)
                        vertex_event_rate = 0.0

            # If the last synapse vertex created had any incoming connections
            if len(vertex.incoming_connections) > 0:
                self.verts.append(vertex)

        logger.debug("\t\t\t%u synapse vertices", len(self.verts))

        # Loop through synapse vertices
        for v in self.verts:
            # Add application to dictionary
            vertex_applications[v] = synapse_app

            # Add resources to dictionary
            # **TODO** add SDRAM
            vertex_resources[v] = { machine.Cores: 1 }

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def partition_matrices(self, matrices, vertex_slice, in_connections):
        # Partition matrices
        sub_matrices = self.regions[Regions.synaptic_matrix].partition_matrices(
            matrices, vertex_slice, in_connections)

        # Place them in memory
        matrix_placements = self.regions[Regions.key_lookup].place_matrices(
            sub_matrices)

        # Return both
        return sub_matrices, matrix_placements

    def get_size(self, post_vertex_slice, sub_matrices, matrix_placements,
                 weight_fixed_point, out_buffers):
        region_arguments = self._get_region_arguments(
            post_vertex_slice, sub_matrices, matrix_placements,
            weight_fixed_point, out_buffers)

        # Calculate region size
        vertex_size_bytes = sizeof_regions_named(self.regions,
                                                 region_arguments)

        logger.debug("\t\t\tRegion size = %u bytes", vertex_size_bytes)
        return vertex_size_bytes

    def write_to_file(self, post_vertex_slice, sub_matrices, matrix_placements,
                      weight_fixed_point, out_buffers, fp):
        region_arguments = self._get_region_arguments(
            post_vertex_slice, sub_matrices, matrix_placements,
            weight_fixed_point, out_buffers)

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
    def _get_region_arguments(self, post_vertex_slice, sub_matrices,
                              matrix_placements, weight_fixed_point, out_buffers):
        region_arguments = defaultdict(Args)

        # Add kwargs for regions that require them
        region_arguments[Regions.system].kwargs["application_words"] =\
            [weight_fixed_point, len(post_vertex_slice)]

        region_arguments[Regions.key_lookup].kwargs["sub_matrices"] =\
            sub_matrices
        region_arguments[Regions.key_lookup].kwargs["matrix_placements"] =\
            matrix_placements

        region_arguments[Regions.synaptic_matrix].kwargs["sub_matrices"] =\
            sub_matrices
        region_arguments[Regions.synaptic_matrix].kwargs["matrix_placements"] =\
            matrix_placements
        region_arguments[Regions.synaptic_matrix].kwargs["weight_fixed_point"] =\
            weight_fixed_point

        region_arguments[Regions.output_buffer].kwargs["out_buffers"] =\
            out_buffers

        return region_arguments
