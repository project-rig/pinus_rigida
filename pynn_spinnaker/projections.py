try:
    from itertools import izip
except ImportError:
    izip = zip  # Python 3 zip returns an iterator already
from pyNN import common
from pyNN.space import Space
from pyNN.standardmodels import StandardCellType
from . import simulator
import logging
import numpy as np
from rig import machine

# Import classes
from collections import namedtuple
from rig.utils.contexts import ContextMixin
from spinnaker.current_input_cluster import CurrentInputCluster
from .standardmodels.synapses import StaticSynapse

# Import functions
from spinnaker.utils import get_model_comparable

logger = logging.getLogger("pynn_spinnaker")

# --------------------------------------------------------------------------
# SynapseClusterType
# --------------------------------------------------------------------------
class SynapseClusterType(namedtuple("SynapseClusterType",
                                    ["model", "receptor"])):
    # Override hash and equality magic methods so synapse
    # cluster types are compared based on compatibility
    def __hash__(self):
        return hash(self._comparable)

    def __eq__(self, other):
        return self._comparable == other._comparable

    def __ne__(self, other):
        return not(self == other)

    @property
    # Concatenate together the receptor type and
    # the comparable tuple of the model
    def _comparable(self):
        return (self.receptor,) + get_model_comparable(self.model)


# --------------------------------------------------------------------------
# Projection
# --------------------------------------------------------------------------
class Projection(common.Projection, ContextMixin):
    __doc__ = common.Projection.__doc__
    _simulator = simulator
    _static_synapse_class = StaticSynapse

    def __init__(self, presynaptic_population, postsynaptic_population,
                 connector, synapse_type, source=None, receptor_type=None,
                 space=Space(), label=None):
        common.Projection.__init__(self, presynaptic_population,
                                   postsynaptic_population, connector,
                                   synapse_type, source, receptor_type,
                                   space, label)

        # Initialise the context stack
        ContextMixin.__init__(self, {})

        # Add projection to simulator
        self._simulator.state.projections.append(self)

        # If pre-synaptic population in an assembly
        if isinstance(self.pre, common.Assembly):
            # Add this projection to each pre-population in
            # assembly's list of outgoing connections
            for p in self.pre.populations:
                p.outgoing_projections.append(self)
        # Otherwise add it to the pre-synaptic population's list
        # **THINK** what about population-views? add to their parent?
        else:
            self.pre.outgoing_projections.append(self)

        # If post-synaptic population in an assembly
        if isinstance(self.post, common.Assembly):
            assert self.post._homogeneous_synapses, (
                "Inhomogeneous assemblies not yet supported")

            # Add this projection to each post-population in
            # assembly's list of incoming connections
            for p in self.post.populations:
                p.incoming_projections[self._synapse_cluster_type][self.pre].append(self)
        # Otherwise add it to the post-synaptic population's list
        # **THINK** what about population-views? add to their parent?
        else:
            self.post.incoming_projections[self._synapse_cluster_type][self.pre].append(self)

    def __len__(self):
        raise NotImplementedError

    def set(self, **attributes):
        raise NotImplementedError

    # --------------------------------------------------------------------------
    # Internal SpiNNaker methods
    # --------------------------------------------------------------------------
    def _build(self, **context_kwargs):
        # **TODO** this may already have been connected
        # by another assembled post population
        # Build each projection, adding the matrix rows to the context
        with self.get_new_context(**context_kwargs):
            self._connector.connect(self)

    def _create_current_input_cluster(self, timer_period_us, simulation_ticks,
                                      vertex_applications, vertex_resources):
        # If this projection is directory connectable
        if self._directly_connectable:
            logger.debug("\t\tProjection:%s", self.label)

            # Find index of receptor type
            receptor_index =\
                self.post.celltype.receptor_types.index(self.receptor_type)

            # Create current input cluster
            self._current_input_cluster = CurrentInputCluster(
                self.pre.celltype, self.pre._parameters, self.pre.initial_values,
                self._simulator.state.dt, timer_period_us, simulation_ticks,
                self.pre.recorder.indices_to_record, self.pre.spinnaker_config,
                receptor_index, vertex_applications, vertex_resources,
                self.current_input_j_constraint)
        # Otherwise, null current input cluster
        else:
            self._current_input_cluster = None

        return self._current_input_cluster

    @ContextMixin.use_contextual_arguments()
    def _direct_convergent_connect(self, presynaptic_indices,
                                   postsynaptic_index, direct_weights,
                                   **connection_parameters):
        # **TODO** one-to-one connections that
        # reshuffle cells COULD be supported
        assert len(presynaptic_indices) == 1
        assert presynaptic_indices[0] == postsynaptic_index

        # Warn if delay doesn't match simulation timestep
        # if connection_parameters["delay"] != self._simulator.state.dt:
        #    logger.warn("Direct connections are treated "
        #                "as having delay of one timestep")

        # Set weight in direct weights array
        direct_weights[postsynaptic_index] =\
            abs(connection_parameters["weight"])

    @ContextMixin.use_contextual_arguments()
    def _synaptic_convergent_connect(self, presynaptic_indices,
                                     postsynaptic_index, matrix_rows,
                                     weight_range, **connection_parameters):
        self.post._convergent_connect(presynaptic_indices, postsynaptic_index,
                                      matrix_rows, weight_range,
                                      **connection_parameters)

    @ContextMixin.use_contextual_arguments()
    def _convergent_connect(self, presynaptic_indices, postsynaptic_index,
                            directly_connect, **connection_parameters):
        # If post-synaptic population in an assembly
        if isinstance(self.post, common.Assembly):
            assert False
        # **TODO** figure out which population within assembly post index
        # relates to Otherwise add it to the post-synaptic population's list
        # **TODO** what about population-views? add to their parent?
        else:
            if directly_connect:
                self._direct_convergent_connect(presynaptic_indices,
                                                postsynaptic_index,
                                                **connection_parameters)
            else:
                self._synaptic_convergent_connect(presynaptic_indices,
                                                  postsynaptic_index,
                                                  **connection_parameters)

    def _build_direct_connection(self):
        # Assert that the connection is directly connectable
        assert self._directly_connectable

        # Create, initially zeroed away of direct connection weights
        direct_weights = np.zeros(self.post.size)

        # Build
        self._build(directly_connect=True, direct_weights=direct_weights)

        return direct_weights

    def _estimate_num_synapses(self, pre_slice, post_slice):
        return self._connector.estimate_num_synapses(
            pre_slice, post_slice, self.pre.size, self.post.size)

    def _load_current_input_verts(self, placements, allocations,
                                  machine_controller):
        # If projection has no current input cluster, skip
        if self._current_input_cluster is None:
            return

        logger.info("\tProjection label:%s from population label:%s",
                    self.label, self.pre.label)

        # Build direct connection for projection
        direct_weights = self._build_direct_connection()

        # Loop through synapse verts
        for v in self._current_input_cluster.verts:
            # Use native S16.15 format
            v.weight_fixed_point = 15

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
                # Allocate two output buffers for this synapse population
                out_buffer_bytes = len(v.post_neuron_slice) * 4
                v.out_buffers = [
                    machine_controller.sdram_alloc(out_buffer_bytes,
                                                   clear=True)
                    for _ in range(2)]

                # Calculate required memory size
                size, allocs = self._current_input_cluster.get_size(
                    v.post_neuron_slice, direct_weights, v.out_buffers)

                # Allocate a suitable memory block
                # for this vertex and get memory io
                # **NOTE** this is tagged by core
                memory_io = machine_controller.sdram_alloc_as_filelike(
                    size, tag=core.start)
                logger.debug("\t\t\tMemory with tag:%u begins at:%08x",
                                core.start, memory_io.address)

                # Write the vertex to file
                v.region_memory = self._current_input_cluster.write_to_file(
                    v.post_neuron_slice, direct_weights, v.out_buffers,
                    memory_io)

    # --------------------------------------------------------------------------
    # Internal SpiNNaker properties
    # --------------------------------------------------------------------------
    @property
    def _synapse_cluster_type(self):
        return SynapseClusterType(self.synapse_type, self.receptor_type)

    @property
    def _directly_connectable(self):
        # If conversion of direct connections is disabled, return false
        if not self._simulator.state.convert_direct_connections:
            return False

        # If the pre-synaptic celltype can be directly connectable,
        # the connector can be reduced to a direct connector and
        # the synapse type is static
        return (self.pre.celltype.directly_connectable and
                self._connector.directly_connectable and
                type(self.synapse_type) is self._static_synapse_class)
