# Import modules
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
from rig.utils.contexts import ContextMixin, Required
from six import iteritems
from spinnaker.neural_population import NeuralPopulation
from spinnaker.synapse_population import SynapsePopulation

# Import functions
from spinnaker.utils import evenly_slice

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



class Population(common.Population, ContextMixin):
    __doc__ = common.Population.__doc__
    _simulator = simulator
    _recorder_class = Recorder
    _assembly_class = Assembly
    
    def __init__(self, size, cellclass, cellparams=None, structure=None,
                 initial_values={}, label=None):
        __doc__ = common.Population.__doc__
        super(Population, self).__init__(size, cellclass, cellparams, structure, initial_values, label)
        
        # Initialise the context stack
        ContextMixin.__init__(self, {})
        
        # Create dictionary of pre-synaptic populations to incoming projections
        self.incoming_projections = defaultdict(lambda: defaultdict(list))

        # Create list of outgoing projections
        self.outgoing_projections = list()
        
        # Add population to simulator
        self._simulator.state.populations.append(self)
    
    def partition(self):
        # Slice population evenly
        # **TODO** pick based on timestep and parameters
        vertex_slices = evenly_slice(self.size,
                                     self.celltype.max_neurons_per_core)

        # Create a resource to accompany each slice
        # **TODO** estimate SDRAM usage for incoming projections
        resources = { machine.Cores: 1 }
        vertex_resources = [resources] * len(vertex_slices)
        return vertex_slices, vertex_resources

    def create_spinnaker_neural_population(self, simulation_timestep_us,
                                           timer_period_us, simulation_ticks):
        if isinstance(self.celltype, StandardCellType):
            parameters = self.celltype.native_parameters
        else:
            parameters = self.celltype.parameter_space
        parameters.shape = (self.size,)
        
        # Create neural population
        return NeuralPopulation(self.celltype, parameters,
                                self.initial_values, simulation_timestep_us,
                                timer_period_us, simulation_ticks,
                                self.recorder.indices_to_record)

    def create_spinnaker_synapse_population(self, weight_fixed_point,
                                            timer_period_us, 
                                            simulation_ticks):
        # Create synapse population
        return SynapsePopulation(weight_fixed_point,
                                 timer_period_us, simulation_ticks)

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

            # Build each projection, adding the matrix rows to the context
            with self.get_new_context(matrix_rows=population_matrix_rows[pre_pop],
                                      weight_range=weight_range):
                for projection in projections:
                    projection.build()

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

    @ContextMixin.use_contextual_arguments()
    def convergent_connect(self, projection, presynaptic_indices,
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
