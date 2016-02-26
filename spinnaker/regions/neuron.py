# Import classes
from parameter_space import ParameterSpace


# ------------------------------------------------------------------------------
# Neuron
# ------------------------------------------------------------------------------
class Neuron(ParameterSpace):
    def __init__(self, cell_type, parameters, initial_values, sim_timestep_ms):
        # Superclass
        super(Neuron, self).__init__(cell_type.neuron_mutable_param_map,
                                     cell_type.neuron_immutable_param_map,
                                     parameters, initial_values,
                                     sim_timestep_ms=sim_timestep_ms)
