# Import modules
import enum
import itertools
import logging
import numpy as np
import regions
from rig import machine

# Import classes
from collections import defaultdict
from utils import Args, InputVertex

# Import functions
from six import iteritems
from utils import (get_model_executable_filename, load_regions, split_slice)

logger = logging.getLogger("pynn_spinnaker")


# ----------------------------------------------------------------------------
# Regions
# ----------------------------------------------------------------------------
class Regions(enum.IntEnum):
    """Region names, corresponding to those defined in `synapse_processor.h`"""
    system = 0
    key_lookup = 1
    synaptic_matrix = 2
    plasticity = 3
    output_buffer = 4
    delay_buffer = 5
    back_prop_input = 6
    profiler = 7
    statistics = 8


# ----------------------------------------------------------------------------
# Vertex
# ----------------------------------------------------------------------------
class Vertex(InputVertex):
    def __init__(self, post_neuron_slice, receptor_index):
        # Superclass
        super(Vertex, self).__init__(post_neuron_slice, receptor_index)

        self.back_prop_in_verts = []

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
        4:  "Process back propagation",
    }

    # Names of statistics
    statistic_names = (
        "row_requested",
        "delay_row_requested",
        "delay_buffers_not_processed",
        "input_buffer_overflows",
        "key_lookup_fails",
    )

    def __init__(self, sim_timestep_ms, timer_period_us, sim_ticks,
                 max_delay_ms, config, post_pop_size, synapse_model,
                 receptor_index, synaptic_projections,
                 vertex_applications, vertex_resources, post_synaptic_width):
        # Dictionary of regions
        self.regions = {}
        self.regions[Regions.system] = regions.System(timer_period_us,
                                                      sim_ticks)
        self.regions[Regions.key_lookup] = regions.KeyLookupBinarySearch()
        self.regions[Regions.output_buffer] = regions.OutputBuffer()
        self.regions[Regions.delay_buffer] = regions.DelayBuffer(
            synapse_model.max_synaptic_event_rate,
            sim_timestep_ms, max_delay_ms)
        self.regions[Regions.back_prop_input] = regions.SDRAMBackPropInput()
        self.regions[Regions.statistics] = regions.Statistics(
            len(self.statistic_names))

        # Create correct type of synaptic matrix region
        self.regions[Regions.synaptic_matrix] =\
            synapse_model.synaptic_matrix_region_class(synapse_model)

        # If synapse mode has a plasticity parameter map
        if hasattr(synapse_model, "plasticity_param_map"):
            self.regions[Regions.plasticity] =\
                regions.HomogeneousParameterSpace(
                    synapse_model.plasticity_param_map,
                    synapse_model.native_parameters,
                    sim_timestep_ms)

        # Add profiler region if required
        if config.num_profile_samples is not None:
            self.regions[Regions.profiler] =\
                regions.Profiler(config.num_profile_samples)

        # Split population slice
        post_slices = split_slice(post_pop_size, post_synaptic_width)

        logger.debug("\t\tSynapse model:%s, Receptor index:%u",
                     synapse_model.__class__.__name__, receptor_index)

        # Get synapse application name
        synapse_app = get_model_executable_filename(
            "synapse_", synapse_model, config.num_profile_samples is not None)
        
        logger.debug("\t\t\tSynapse application:%s", synapse_app)

        # Loop through the post-slices
        self.verts = []
        for post_slice in post_slices:
            logger.debug("\t\t\tPost slice:%s", str(post_slice))

            # Loop through all non-directly connectable
            # projections of this type
            vert_event_rate = 0.0
            vert = Vertex(post_slice, receptor_index)
            for proj in synaptic_projections:
                logger.debug("\t\t\t\tProjection:%s", proj.label)
                # Loop through the vertices which the pre-synaptic
                # population has been partitioned into
                for pre_vertex in proj.pre._neural_cluster.verts:
                    logger.debug("\t\t\t\t\tPre slice:%s",
                                 str(pre_vertex.neuron_slice))

                    # Estimate number of synapses the connection between
                    # The pre and the post-slice of neurons will contain
                    total_synapses = proj._estimate_num_synapses(
                        pre_vertex.neuron_slice, post_slice)

                    # If this projection doesn't result in any
                    # synapses don't add connection
                    if total_synapses == 0:
                        logger.debug("\t\t\t\t\t\tNo synapses")
                        continue

                    # Use this to calculate event rate
                    pre_mean_rate = proj.pre.spinnaker_config.mean_firing_rate
                    pre_rate = total_synapses * pre_mean_rate

                    # **TODO** SDRAM estimation
                    logger.debug("\t\t\t\t\t\tTotal synapses:%d, "
                                 "synaptic event rate:%f",
                                 total_synapses, pre_rate)

                    # Add this connection to the synapse vertex
                    vert.add_connection(proj.pre, pre_vertex)

                    # Add event rate to total for current synapse processor
                    vert_event_rate += pre_rate

                    # If it's more than this type of
                    # synapse processor can handle
                    if vert_event_rate > synapse_model.max_synaptic_event_rate:
                        # Add current synapse vertex to list
                        self.verts.append(vert)

                        # Create replacement and reset event rate
                        vert = Vertex(post_slice, receptor_index)
                        vert_event_rate = 0.0

            # If the last synapse vertex created had any incoming connections
            if len(vert.incoming_connections) > 0:
                self.verts.append(vert)

        logger.debug("\t\t\t%u synapse vertices", len(self.verts))

        # Loop through synapse vertices
        for v in self.verts:
            # Add application to dictionary
            vertex_applications[v] = synapse_app

            # Add resources to dictionary
            # **TODO** add SDRAM
            vertex_resources[v] = {machine.Cores: 1}

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def allocate_out_buffers(self, placements, allocations,
                             machine_controller):
        # Loop through synapse verts
        for v in self.verts:
            # Get placement and allocation
            vertex_placement = placements[v]
            vertex_allocation = allocations[v]

            # Get core this vertex should be run on
            core = vertex_allocation[machine.Cores]
            assert (core.stop - core.start) == 1

            logger.debug("\t\tVertex %s (%u, %u, %u)",
                         v, vertex_placement[0], vertex_placement[1],
                         core.start)

            # Select placed chip
            with machine_controller(x=vertex_placement[0],
                                    y=vertex_placement[1]):
                # Allocate two output buffers
                # for this synapse population
                out_buffer_bytes = len(v.post_neuron_slice) * 4
                v.out_buffers = [
                    machine_controller.sdram_alloc(out_buffer_bytes,
                                                   clear=True)
                    for _ in range(2)]

    def load(self, placements, allocations, machine_controller,
             matrices, weight_fixed_point, flush_mask):
        # Loop through synapse verts
        for v in self.verts:
            # Cache weight fixed-point for
            # this synapse point in vertex
            v.weight_fixed_point = weight_fixed_point

            # Get placement and allocation
            vertex_placement = placements[v]
            vertex_allocation = allocations[v]

            # Get core this vertex should be run on
            core = vertex_allocation[machine.Cores]
            assert (core.stop - core.start) == 1

            logger.debug("\t\tVertex %s (%u, %u, %u)",
                         v, vertex_placement[0], vertex_placement[1],
                         core.start)

            # Partition matrices
            sub_matrix_props, sub_matrix_rows =\
                self.regions[Regions.synaptic_matrix].partition_matrices(
                    matrices, v.post_neuron_slice, v.incoming_connections)

            # Place them in memory
            matrix_placements = self.regions[Regions.key_lookup].place_matrices(
                sub_matrix_props)

            # Select placed chip
            with machine_controller(x=vertex_placement[0],
                                    y=vertex_placement[1]):
                # Get the back propagation buffers from 
                # each back-propagating neuron vertex
                back_prop_in_buffers = [
                    b.get_back_prop_in_buffer(v.post_neuron_slice)
                    for b in v.back_prop_in_verts]

                # Get region arguments required to calculate size and write
                region_arguments = self._get_region_arguments(
                    v.post_neuron_slice, sub_matrix_props, sub_matrix_rows,
                    matrix_placements, weight_fixed_point, v.out_buffers,
                    back_prop_in_buffers, flush_mask)

                # Load regions
                v.region_memory = load_regions(self.regions, region_arguments,
                                               machine_controller, core)

                # Store sub matrix properties and placements in vertex so
                # they can be used to subsequently read weights back
                v.sub_matrix_props = sub_matrix_props
                v.matrix_placements = matrix_placements

    def read_profile(self):
        # Get the profile recording region
        region = self.regions[Regions.profiler]

        # Return profile data for each vertex that makes up population
        return [(v.post_neuron_slice.python_slice,
                 region.read_profile(v.region_memory[Regions.profiler],
                                     self.profiler_tag_names))
                for v in self.verts]

    def read_statistics(self):
        # Get the statistics recording region
        region = self.regions[Regions.statistics]

        # Convert stats to numpy array
        np_stats = np.asarray([region.read_stats(v.region_memory[Regions.statistics])
                            for v in self.verts])
        # Convert stats into record array
        stat_names = ",".join(self.statistic_names)
        stat_format = ",".join(
            itertools.repeat("u4", len(self.statistic_names)))
        return np.core.records.fromarrays(np_stats.T, names=stat_names,
                                          formats=stat_format)

    def read_synaptic_matrices(self, pre_pop, names):
        # Get the synaptic matrix region
        region = self.regions[Regions.synaptic_matrix]

        # Loop through synapse vertices (post-synaptic)
        sub_matrices = []
        for post_s_vert in self.verts:
            # If this synapse vertex has no incoming connections
            # from pre-synaptic population, skip
            if pre_pop not in post_s_vert.incoming_connections:
                continue

            # Get region memory for synaptic matrix
            region_mem = post_s_vert.region_memory[Regions.synaptic_matrix]

            # Loop through list of pre-synaptic vertices
            # this synapse vertex is connected to
            for pre_n_vert in post_s_vert.incoming_connections[pre_pop]:
                # Read associated sub-matrix
                sub_matrices.append(region.read_sub_matrix(
                    pre_n_vert, post_s_vert, names, region_mem))

        return sub_matrices

    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _get_region_arguments(self, post_vertex_slice, sub_matrix_props,
                              sub_matrix_rows, matrix_placements,
                              weight_fixed_point, out_buffers,
                              back_prop_in_buffers, flush_mask):
        region_arguments = defaultdict(Args)

        # Add kwargs for regions that require them
        region_arguments[Regions.system].kwargs["application_words"] =\
            [weight_fixed_point, len(post_vertex_slice), flush_mask]

        region_arguments[Regions.key_lookup].kwargs["sub_matrix_props"] =\
            sub_matrix_props
        region_arguments[Regions.key_lookup].kwargs["matrix_placements"] =\
            matrix_placements

        region_arguments[Regions.synaptic_matrix].kwargs["sub_matrix_props"] =\
            sub_matrix_props
        region_arguments[Regions.synaptic_matrix].kwargs["sub_matrix_rows"] =\
            sub_matrix_rows
        region_arguments[Regions.synaptic_matrix].kwargs["matrix_placements"] =\
            matrix_placements
        region_arguments[Regions.synaptic_matrix].kwargs["weight_fixed_point"] =\
            weight_fixed_point

        region_arguments[Regions.output_buffer].kwargs["out_buffers"] =\
            out_buffers

        region_arguments[Regions.delay_buffer].kwargs["sub_matrix_props"] =\
            sub_matrix_props

        region_arguments[Regions.plasticity].kwargs["weight_fixed_point"] =\
            weight_fixed_point

        region_arguments[Regions.back_prop_input].kwargs["back_prop_in_buffers"] =\
            back_prop_in_buffers

        return region_arguments
