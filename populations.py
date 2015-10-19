# Import modules
import numpy
from rig import machine
from pyNN import common

# Import classes
from pyNN.standardmodels import StandardCellType
from pyNN.parameters import ParameterSpace, simplify
from . import simulator
from .recording import Recorder
from rig.utils.contexts import ContextMixin, Required
from spinnaker.neural_population import NeuralPopulation
from utils import evenly_slice

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
        
        # Create empty list to hold incoming projections
        self.incoming_projections = []
        
        # Add population to simulator
        self._simulator.state.populations.append(self)
    
    def partition(self):
        # Slice population evenly
        # **TODO** pick based on timestep and neuron model
        neurons_per_vertex = NeuralPopulation.MAX_CELLS
        vertex_slices = evenly_slice(self.size, neurons_per_vertex)

        # Create a resource to accompany each slice
        # **TODO** estimate SDRAM usage for incoming projections
        resources = { machine.Cores: 1 }
        vertex_resources = [resources] * len(vertex_slices)
        return vertex_slices, vertex_resources

    def create_spinnaker_population(self, simulation_timestep_us, 
                                    hardware_timestep_us, 
                                    duration_timestep):
        if isinstance(self.celltype, StandardCellType):
            parameter_space = self.celltype.native_parameters
        else:
            parameter_space = self.celltype.parameter_space
        parameter_space.shape = (self.size,)

        # Evaluate parameter space
        parameter_space.evaluate(simplify=False)
        
        # **TODO** pick correct population class
        return self.get_new_context(spinnaker_population=NeuralPopulation(
            self.celltype, parameter_space, simulation_timestep_us, hardware_timestep_us, duration_timestep))

    @ContextMixin.use_contextual_arguments()
    def expand_incoming_connection(self, spinnaker_population):
        # Build incoming projections
        # **NOTE** this will result to multiple calls to convergent_connect
        for i in self.incoming_projections:
            i.build()
            
    @ContextMixin.use_contextual_arguments()
    def spinnaker_population(self, spinnaker_population):
        return spinnaker_population
    
    @ContextMixin.use_contextual_arguments()
    def convergent_connect(self, projection, presynaptic_indices, postsynaptic_index,
                            spinnaker_population, **connection_parameters):
        # Create connections within spinnaker population
        spinnaker_population.convergent_connect(projection, presynaptic_indices, 
                                                      postsynaptic_index,
                                                      **connection_parameters)
        
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
