# Import modules
import itertools
import logging
import math
import numpy
import sys
from rig import machine
from pyNN import common

# Import classes
from collections import defaultdict, namedtuple
from operator import itemgetter
from pyNN.standardmodels import StandardCellType
from pyNN.parameters import ParameterSpace, simplify
from . import simulator
from .recording import Recorder
from rig.utils.contexts import ContextMixin
from six import (iteritems, itervalues)
from spinnaker.neural_cluster import NeuralCluster
from spinnaker.synapse_cluster import SynapseCluster

logger = logging.getLogger("pinus_rigida")

Synapse = namedtuple("Synapse", ["weight", "delay", "index"])

class Assembly(common.Assembly):
    _simulator = simulator


class PopulationView(common.PopulationView):
    _assembly_class = Assembly
    _simulator = simulator

    def _get_parameters(self, *names):
        """
        return a ParameterSpace containing native parameters
        """
        parameter_dict = {}
        for name in names:
            value = self.parent._parameters[name]
            if isinstance(value, numpy.ndarray):
                value = value[self.mask]
            parameter_dict[name] = simplify(value)
        return ParameterSpace(parameter_dict, shape=(self.size,)) # or local size?

    def _set_parameters(self, parameter_space):
        """parameter_space should contain native parameters"""
        #ps = self.parent._get_parameters(*self.celltype.get_native_names())
        for name, value in parameter_space.items():
            self.parent._parameters[name][self.mask] = value.evaluate(simplify=True)
            #ps[name][self.mask] = value.evaluate(simplify=True)
        #ps.evaluate(simplify=True)
        #self.parent._parameters = ps.as_dict()

    def _set_initial_value_array(self, variable, initial_values):
        pass

    def _get_view(self, selector, label=None):
        return PopulationView(self, selector, label)



class Population(common.Population):
    __doc__ = common.Population.__doc__
    _simulator = simulator
    _recorder_class = Recorder
    _assembly_class = Assembly
    
    def __init__(self, size, cellclass, cellparams=None, structure=None,
                 initial_values={}, label=None):
        __doc__ = common.Population.__doc__
        super(Population, self).__init__(size, cellclass, cellparams, structure, initial_values, label)

        # Create dictionary of pre-synaptic populations to incoming projections
        self.incoming_projections = defaultdict(lambda: defaultdict(list))

        # Create list of outgoing projections
        self.outgoing_projections = list()
        
        # Add population to simulator
        self._simulator.state.populations.append(self)
    
    def create_neural_cluster(self, pop_id, simulation_timestep_us, timer_period_us,
                              simulation_ticks, vertex_applications,
                              vertex_resources, keyspace):
        # Extract parameter lazy array
        if isinstance(self.celltype, StandardCellType):
            parameters = self.celltype.native_parameters
        else:
            parameters = self.celltype.parameter_space
        parameters.shape = (self.size,)
        
        # Create neural cluster
        return NeuralCluster(pop_id, self.celltype, parameters,
                             self.initial_values, simulation_timestep_us,
                             timer_period_us, simulation_ticks,
                             self.recorder.indices_to_record,
                             self.spinnaker_config, vertex_applications,
                             vertex_resources, keyspace)

    def create_synapse_clusters(self, timer_period_us, simulation_ticks,
                                vertex_applications, vertex_resources):
        # Get neuron clusters dictionary from simulator
        # **THINK** is it better to get this as ANOTHER parameter
        pop_neuron_clusters = self._simulator.state.pop_neuron_clusters

        # Loop through newly partioned incoming projections
        synapse_clusters = {}
        for synapse_type, pre_pop_projections in iteritems(self.incoming_projections):
            # Chain together incoming projections from all populations
            projections = list(itertools.chain.from_iterable(itervalues(pre_pop_projections)))
            synaptic_projections = [p for p in projections
                                    if not p.directly_connectable]

            # Find index of receptor type
            receptor_index = self.celltype.receptor_types.index(synapse_type[1])

            # Create synapse cluster
            c = SynapseCluster(timer_period_us, simulation_ticks,
                               self.spinnaker_config, self.size,
                               synapse_type[0], receptor_index,
                               synaptic_projections, pop_neuron_clusters,
                               vertex_applications, vertex_resources)

            # Add cluster to dictionary
            synapse_clusters[synapse_type] = c

        # Return synapse clusters
        return synapse_clusters

    def build_incoming_connection(self, synapse_type):
        population_matrix_rows = {}
        
        # Create list to hold min and max weight
        # **NOTE** needs to be a list rather than a tuple so it's mutable
        weight_range = [sys.float_info.max, sys.float_info.min]
        
        # Build incoming projections
        # **NOTE** this will result to multiple calls to convergent_connect
        for pre_pop, projections in iteritems(self.incoming_projections[synapse_type]):
            # Create an array to hold matrix rows and initialize each one with an empty list
            population_matrix_rows[pre_pop] = numpy.empty(pre_pop.size, dtype=object)
            
            for r in range(pre_pop.size):
                population_matrix_rows[pre_pop][r] = []

            # Loop through projections and build
            for projection in projections:
                projection.build(matrix_rows=population_matrix_rows[pre_pop],
                                    weight_range=weight_range,
                                    directly_connect=False)

            # Sort each row in matrix by post-synaptic neuron
            # **THINK** is this necessary or does
            # PyNN always move left to right
            for r in population_matrix_rows[pre_pop]:
                r.sort(key=itemgetter(2))

        # Get MSB of minimum and maximum weight and get magnitude of range
        weight_msb = [math.floor(math.log(r, 2)) + 1
                    for r in weight_range]
        weight_range = weight_msb[1] - weight_msb[0]

        # Check there's enough bits to represent this is any form
        assert weight_range < 16

        # Calculate where the weight format fixed-point lies
        weight_fixed_point = 16 - int(weight_msb[1])
        logger.debug("\t\tWeight fixed point:%u" % weight_fixed_point)

        return population_matrix_rows, weight_fixed_point

    def convergent_connect(self, presynaptic_indices,
                           postsynaptic_index, matrix_rows,
                           weight_range, **connection_parameters):
        # Extract connection parameters
        weight = abs(connection_parameters["weight"])
        delay = connection_parameters["delay"]

        # Update incoming weight range
        weight_range[0] = min(weight_range[0], weight)
        weight_range[1] = max(weight_range[1], weight)
        
        # Add synapse to each row
        for p in matrix_rows[presynaptic_indices]:
            p.append(Synapse(weight, delay, postsynaptic_index))

    def get_neural_profile_data(self):
        # Assert that profiling is enabled
        assert self.spinnaker_config.get("profile_samples", None) is not None

        # Read profile from neuron cluster
        return self._simulator.state.pop_neuron_clusters[self].read_profile()

    def get_synapse_profile_data(self):
        # Assert that profiling is enabled
        assert self.spinnaker_config.get("profile_samples", None) is not None

        # Read profile from synapse cluster
        return self._simulator.state.pop_synapse_clusters[self].read_profile()

    def _create_cells(self):
        id_range = numpy.arange(simulator.state.id_counter,
                                simulator.state.id_counter + self.size)
        self.all_cells = numpy.array([simulator.ID(id) for id in id_range],
                                     dtype=simulator.ID)
        
        # In terms of MPI, all SpiNNaker neurons are local
        self._mask_local = numpy.ones((self.size,), bool)
        
        for id in self.all_cells:
            id.parent = self
        simulator.state.id_counter += self.size

    def _set_initial_value_array(self, variable, initial_values):
        pass

    def _get_view(self, selector, label=None):
        return PopulationView(self, selector, label)

    def _get_parameters(self, *names):
        """
        return a ParameterSpace containing native parameters
        """
        parameter_dict = {}
        for name in names:
            parameter_dict[name] = simplify(self._parameters[name])
        return ParameterSpace(parameter_dict, shape=(self.local_size,))

    def _set_parameters(self, parameter_space):
        """parameter_space should contain native parameters"""
        #ps = self._get_parameters(*self.celltype.get_native_names())
        #ps.update(**parameter_space)
        #ps.evaluate(simplify=True)
        #self._parameters = ps.as_dict()
        parameter_space.evaluate(simplify=False, mask=self._mask_local)
        for name, value in parameter_space.items():
            self._parameters[name] = value

    @property
    def spinnaker_config(self):
        # **TODO** merge in celltype config
        return self._simulator.state.config[self]

    @property
    def entirely_directly_connectable(self):
        # If conversion of direct connections is disabled, return false
        if not self._simulator.state.convert_direct_connections:
            return False
        
        # If cell type isn't directly connectable, the population can't be
        if not self.celltype.directly_connectable:
            return False

        # If none of the outgoing projections aren't directly connectable!
        return not any([not o._connector.directly_connectable
                        for o in self.outgoing_projections])

