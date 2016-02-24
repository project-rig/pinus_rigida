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
from six import iteritems, itervalues
from spinnaker.neural_cluster import NeuralCluster
from spinnaker.synapse_cluster import SynapseCluster
from spinnaker.spinnaker_population_config import SpinnakerPopulationConfig

logger = logging.getLogger("pinus_rigida")

Synapse = namedtuple("Synapse", ["weight", "delay", "index"])

# --------------------------------------------------------------------------
# WeightRange
# --------------------------------------------------------------------------
class WeightRange(object):
    def __init__(self):
        self.min = sys.float_info.max
        self.max = sys.float_info.min

    def update(self, weight):
        self.min = min(self.min, weight)
        self.max = max(self.max, weight)

    @property
    def fixed_point(self):
        # Get MSB of minimum and maximum weight and
        min_msb = math.floor(math.log(self.min, 2)) + 1
        max_msb = math.floor(math.log(self.max, 2)) + 1

        # Check there's enough bits to represent this range in 16 bits
        assert (max_msb - min_msb) < 16

        # Calculate where the weight format fixed-point lies
        return (16 - int(max_msb))

# Round a j constraint to the lowest power-of-two
# multiple of the minium j constraint
def round_j_constraint(j_constraint, min_j_constraint):
    return min_j_constraint * int(2 ** math.floor(
        math.log(j_constraint / min_j_constraint, 2)))

# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------
class Assembly(common.Assembly):
    _simulator = simulator


# --------------------------------------------------------------------------
# PopulationView
# --------------------------------------------------------------------------
class PopulationView(common.PopulationView):
    _assembly_class = Assembly
    _simulator = simulator

    # --------------------------------------------------------------------------
    # Internal PyNN methods
    # --------------------------------------------------------------------------
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
        raise NotImplementedError()

    def _set_initial_value_array(self, variable, initial_values):
        # Initial values are handled by common.Population
        # so we can evaluate them at build-time
        pass

    def _get_view(self, selector, label=None):
        return PopulationView(self, selector, label)


# --------------------------------------------------------------------------
# Population
# --------------------------------------------------------------------------
class Population(common.Population):
    __doc__ = common.Population.__doc__
    _simulator = simulator
    _recorder_class = Recorder
    _assembly_class = Assembly
    
    def __init__(self, size, cellclass, cellparams=None, structure=None,
                 initial_values={}, label=None):
        __doc__ = common.Population.__doc__
        super(Population, self).__init__(size, cellclass, cellparams, structure, initial_values, label)

        # Create a spinnaker config
        self.spinnaker_config = SpinnakerPopulationConfig()

        # Dictionary mapping pre-synaptic populations to
        # incoming projections, subdivided by synapse type
        # {synapse_cluster_type: {pynn_population: [pynn_projection]}}
        self.incoming_projections = defaultdict(lambda: defaultdict(list))

        # List of outgoing projections from this population
        # [pynn_projection]
        self.outgoing_projections = list()
        
        # Add population to simulator
        self._simulator.state.populations.append(self)
    
    # --------------------------------------------------------------------------
    # Public SpiNNaker methods
    # --------------------------------------------------------------------------
    def get_neural_profile_data(self):
        logger.info("Downloading neural profile for population %s",
                    self.label)

        # Assert that profiling is enabled
        assert self.spinnaker_config.num_profile_samples is not None

        # Read profile from neuron cluster
        return self._simulator.state.pop_neuron_clusters[self].read_profile()

    def get_synapse_profile_data(self):
        logger.info("Downloading synapse profile for population %s",
                    self.label)

        # Assert that profiling is enabled
        assert self.spinnaker_config.num_profile_samples is not None

        # Read profile from each synapse cluster
        s_clusters = self._simulator.state.pop_synapse_clusters[self]
        return {t: c.read_profile() for t, c in iteritems(s_clusters)}

    # --------------------------------------------------------------------------
    # Internal PyNN methods
    # --------------------------------------------------------------------------
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
        # Initial values are handled by common.Population
        # so we can evaluate them at build-time
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
        raise NotImplementedError()

    # --------------------------------------------------------------------------
    # Internal SpiNNaker methods
    # --------------------------------------------------------------------------
    def _estimate_constraints(self, hardware_timestep_us):
        # Determine the fraction of 1ms that the hardware timestep is.
        # This is used to scale all time-driven estimates
        timestep_multiplier = min(1.0, float(hardware_timestep_us) / 1000.0)
        logger.debug("\t\tTimestep multiplier:%f", timestep_multiplier)

        # **TODO** incorporate firing rate annotation in sane way

        # Apply both multipliers to the hard maximum specified in celltype
        self.neuron_j_constraint = int(self.celltype.max_neurons_per_core *
                                       timestep_multiplier)
        logger.debug("\t\tNeuron j constraint:%u",
                     self.neuron_j_constraint)

        self.synapse_j_constraints = {}
        for synapse_type, pre_pop_projections in iteritems(self.incoming_projections):
            # Chain together incoming projections from all populations
            projections = list(itertools.chain.from_iterable(itervalues(pre_pop_projections)))
            synaptic_projections = [p for p in projections
                                    if not p._directly_connectable]

            logger.debug("\t\tSynapse type:%s - Synapse j constraint:%u",
                         synapse_type[0],
                         synapse_type[0].max_post_neurons_per_core)
            self.synapse_j_constraints[synapse_type] =\
                synapse_type[0].max_post_neurons_per_core

        # Find the minimum constraint in j
        min_j_constraint = min(self.neuron_j_constraint,
                               *itervalues(self.synapse_j_constraints))

        logger.debug("\t\tMin j constraint:%u", min_j_constraint)

        # Round j constraints to multiples of minimum
        self.neuron_j_constraint = round_j_constraint(
            self.neuron_j_constraint, min_j_constraint)

        self.synapse_j_constraints = {
            t: round_j_constraint(c, min_j_constraint)
            for t, c in iteritems(self.synapse_j_constraints)}

        # Now determin the maximum constraint i.e. the 'width'
        # that will be constrained together
        max_j_constraint = max(self.neuron_j_constraint,
                               *itervalues(self.synapse_j_constraints))

        # Calculate how many cores this means will be required
        num_cores = (max_j_constraint / self.neuron_j_constraint) +\
            sum(max_j_constraint / c for c in itervalues(self.synapse_j_constraints))

        # Check that this will fit on a chip
        # **TODO** iterate, dividing maximum constraint by 2
        assert num_cores <= 16

        logger.debug("\t\tNeuron j constraint:%u", self.neuron_j_constraint)
        for synapse_type, synapse_j_constrain in iteritems(self.synapse_j_constraints):
            logger.debug("\t\tSynapse type:%s - J constraint:%u",
                         synapse_type, synapse_j_constrain)

    def _create_neural_cluster(self, pop_id, simulation_timestep_us, timer_period_us,
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
                             vertex_resources, keyspace,
                             self.neuron_j_constraint)

    def _create_synapse_clusters(self, timer_period_us, simulation_ticks,
                                vertex_applications, vertex_resources):
        # Get neuron clusters dictionary from simulator
        # **THINK** is it better to get this as ANOTHER parameter
        pop_neuron_clusters = self._simulator.state.pop_neuron_clusters

        # Loop through newly partioned incoming projections_load_synapse_verts
        synapse_clusters = {}
        for synapse_type, pre_pop_projections in iteritems(self.incoming_projections):
            # Chain together incoming projections from all populations
            projections = list(itertools.chain.from_iterable(itervalues(pre_pop_projections)))
            synaptic_projections = [p for p in projections
                                    if not p._directly_connectable]

            # Find index of receptor type
            receptor_index = self.celltype.receptor_types.index(synapse_type[1])

            # Create synapse cluster
            c = SynapseCluster(timer_period_us, simulation_ticks,
                               self.spinnaker_config, self.size,
                               synapse_type[0], receptor_index,
                               synaptic_projections, pop_neuron_clusters,
                               vertex_applications, vertex_resources,
                               self.synapse_j_constraints[synapse_type])

            # Add cluster to dictionary
            synapse_clusters[synapse_type] = c

        # Return synapse clusters
        return synapse_clusters

    def _build_incoming_connection(self, synapse_type):
        population_matrix_rows = {}
        
        # Create weight range object to track range of
        # weights present in incoming connections
        weight_range = WeightRange()
        
        # Build incoming projections
        # **NOTE** this will result to multiple calls to convergent_connect
        for pre_pop, projections in iteritems(self.incoming_projections[synapse_type]):
            # Create an array to hold matrix rows and initialize each one with an empty list
            population_matrix_rows[pre_pop] = numpy.empty(pre_pop.size, dtype=object)
            for r in range(pre_pop.size):
                population_matrix_rows[pre_pop][r] = []

            # Loop through projections and build
            for projection in projections:
                projection._build(matrix_rows=population_matrix_rows[pre_pop],
                                  weight_range=weight_range,
                                  directly_connect=False)

            # Sort each row in matrix by post-synaptic neuron
            # **THINK** is this necessary or does
            # PyNN always move left to right
            for r in population_matrix_rows[pre_pop]:
                r.sort(key=itemgetter(2))

        # Calculate where the weight format fixed-point lies
        weight_fixed_point = weight_range.fixed_point
        logger.debug("\t\tWeight fixed point:%u", weight_fixed_point)

        return population_matrix_rows, weight_fixed_point

    def _convergent_connect(self, presynaptic_indices,
                           postsynaptic_index, matrix_rows,
                           weight_range, **connection_parameters):
        # Extract connection parameters
        weight = abs(connection_parameters["weight"])
        delay = connection_parameters["delay"]

        # Update incoming weight range
        weight_range.update(weight)
        
        # Add synapse to each row
        for p in matrix_rows[presynaptic_indices]:
            p.append(Synapse(weight, delay, postsynaptic_index))

    # --------------------------------------------------------------------------
    # Internal SpiNNaker properties
    # --------------------------------------------------------------------------
    @property
    def _entirely_directly_connectable(self):
        # If conversion of direct connections is disabled, return false
        if not self._simulator.state.convert_direct_connections:
            return False
        
        # If cell type isn't directly connectable, the population can't be
        if not self.celltype.directly_connectable:
            return False

        # If none of the outgoing projections aren't directly connectable!
        return not any([not o._connector.directly_connectable
                        for o in self.outgoing_projections])

