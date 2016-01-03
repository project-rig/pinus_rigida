from itertools import repeat
try:
    from itertools import izip
except ImportError:
    izip = zip  # Python 3 zip returns an iterator already
from pyNN import common
from pyNN.core import ezip
from pyNN.parameters import ParameterSpace
from pyNN.space import Space
from . import simulator

class Projection(common.Projection):
    __doc__ = common.Projection.__doc__
    _simulator = simulator

    def __init__(self, presynaptic_population, postsynaptic_population,
                 connector, synapse_type, source=None, receptor_type=None,
                 space=Space(), label=None):
        common.Projection.__init__(self, presynaptic_population, postsynaptic_population,
                                   connector, synapse_type, source, receptor_type,
                                   space, label)
        
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
                p.incoming_projections[self.spinnaker_synapse_type][self.pre].append(self)
        # Otherwise add it to the post-synaptic population's list
        # **THINK** what about population-views? add to their parent?
        else:
            self.post.incoming_projections[self.spinnaker_synapse_type][self.pre].append(self)
    
    def build(self):
        # connect the populations
        # **TODO** this may already have been connected by another assembled post population
        self._connector.connect(self)
    
    def __len__(self):
        raise NotImplementedError

    def set(self, **attributes):
        #parameter_space = ParameterSpace
        raise NotImplementedError

    def _convergent_connect(self, presynaptic_indices, postsynaptic_index,
                            **connection_parameters):
        # If post-synaptic population in an assembly
        if isinstance(self.post, common.Assembly):
            assert False
            
            #**TODO** figure out which population within assembly post index relates to
        # Otherwise add it to the post-synaptic population's list
        # **TODO** what about population-views? add to their parent?
        else:
            self.post.convergent_connect(self, presynaptic_indices, postsynaptic_index, **connection_parameters)

    def estimate_num_synapses(self, pre_slice, post_slice):
        return self._connector.estimate_num_synapses(pre_slice, post_slice)

    @property
    def spinnaker_synapse_type(self):
        return (self.synapse_type.__class__, self.receptor_type)

    @property
    def directly_connectable(self):
        # If the pre-synaptic celltype can be directly connectable,
        # the connector can be reduced to a direct connector and
        # the synapse type is static
        return (self.pre.celltype.directly_connectable and
                self._connector.directly_connectable and
                self.synapse_type == self._static_synapse_class)
