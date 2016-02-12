from itertools import repeat
try:
    from itertools import izip
except ImportError:
    izip = zip  # Python 3 zip returns an iterator already
from pyNN import common
from pyNN.core import ezip
from pyNN.parameters import ParameterSpace
from pyNN.space import Space
from pyNN.standardmodels import StandardCellType
from . import simulator

from .standardmodels.synapses import StaticSynapse

import logging
import numpy as np

from rig.utils.contexts import ContextMixin, Required

from spinnaker.current_input_cluster import CurrentInputCluster

logger = logging.getLogger("pinus_rigida")

class Projection(common.Projection, ContextMixin):
    __doc__ = common.Projection.__doc__
    _simulator = simulator
    _static_synapse_class = StaticSynapse

    def __init__(self, presynaptic_population, postsynaptic_population,
                 connector, synapse_type, source=None, receptor_type=None,
                 space=Space(), label=None):
        common.Projection.__init__(self, presynaptic_population, postsynaptic_population,
                                   connector, synapse_type, source, receptor_type,
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
            assert self.post._homogeneous_synapses, "Inhomogeneous assemblies not yet supported"
            
            # Add this projection to each post-population in 
            # assembly's list of incoming connections
            for p in self.post.populations:
                p.incoming_projections[self.synapse_cluster_type][self.pre].append(self)
        # Otherwise add it to the post-synaptic population's list
        # **THINK** what about population-views? add to their parent?
        else:
            self.post.incoming_projections[self.synapse_cluster_type][self.pre].append(self)
    
    def build(self, **context_kwargs):
        # connect the populations
        # **TODO** this may already have been connected by another assembled post population
         # Build each projection, adding the matrix rows to the context
        with self.get_new_context(**context_kwargs):
            self._connector.connect(self)
    
    def __len__(self):
        raise NotImplementedError

    def set(self, **attributes):
        #parameter_space = ParameterSpace
        raise NotImplementedError

    # JH: Also _score
    def create_current_input_cluster(self, simulation_timestep_us,
                                      timer_period_us, simulation_ticks,
                                      vertex_applications, vertex_resources):
        # Assert that this projection can be directly connected
        assert self.directly_connectable

        # Extract parameter lazy array for pre-synaptic population
        if isinstance(self.pre.celltype, StandardCellType):
            pre_parameters = self.pre.celltype.native_parameters
        else:
            pre_parameters = self.pre.celltype.parameter_space
        pre_parameters.shape = (self.pre.size,)

        # Find index of receptor type
        receptor_index = self.post.celltype.receptor_types.index(self.receptor_type)

        # Create current input cluster
        return CurrentInputCluster(
            self.pre.celltype, pre_parameters, self.pre.initial_values,
            simulation_timestep_us, timer_period_us, simulation_ticks,
            self.pre.recorder.indices_to_record, self.pre.spinnaker_config,
            receptor_index, vertex_applications, vertex_resources)

    @ContextMixin.use_contextual_arguments()
    def _direct_convergent_connect(self, presynaptic_indices,
                                   postsynaptic_index, direct_weights,
                                   **connection_parameters):
        # **TODO** one-to-one connections that reshuffle cells COULD be supported
        assert len(presynaptic_indices) == 1
        assert presynaptic_indices[0] == postsynaptic_index

        # Warn if delay doesn't match simulation timestep
        #if connection_parameters["delay"] != self._simulator.state.dt:
        #    logger.warn("Direct connections are treated as having delay of one timestep")

        # Set weight in direct weights array
        direct_weights[postsynaptic_index] = abs(connection_parameters["weight"])

    @ContextMixin.use_contextual_arguments()
    def _synaptic_convergent_connect(self, presynaptic_indices,
                                   postsynaptic_index, matrix_rows,
                                   weight_range, **connection_parameters):
        self.post.convergent_connect(presynaptic_indices, postsynaptic_index,
                                     matrix_rows, weight_range,
                                     **connection_parameters)

    @ContextMixin.use_contextual_arguments()
    def _convergent_connect(self, presynaptic_indices, postsynaptic_index,
                            directly_connect, **connection_parameters):
        # If post-synaptic population in an assembly
        if isinstance(self.post, common.Assembly):
            assert False
        #**TODO** figure out which population within assembly post index relates to
        # Otherwise add it to the post-synaptic population's list
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

    def build_direct_connection(self):
        # Assert that the connection is directly connectable
        assert self.directly_connectable

        # Create, initially zeroed away of direct connection weights
        direct_weights = np.zeros(self.post.size)

        # Build
        self.build(directly_connect=True, direct_weights=direct_weights)

        return direct_weights

    def estimate_num_synapses(self, pre_slice, post_slice):
        return self._connector.estimate_num_synapses(pre_slice, post_slice)

    @property
    def synapse_cluster_type(self):
        return (self.synapse_type.__class__, self.receptor_type)

    @property
    def directly_connectable(self):
        # If conversion of direct connections is disabled, return false
        if not self._simulator.state.convert_direct_connections:
            return False
        
        # If the pre-synaptic celltype can be directly connectable,
        # the connector can be reduced to a direct connector and
        # the synapse type is static
        #return False
        return (self.pre.celltype.directly_connectable and
                self._connector.directly_connectable and
                type(self.synapse_type) is self._static_synapse_class)
