# Import classes
from parameter_space import ParameterSpace


# ------------------------------------------------------------------------------
# Synapse
# ------------------------------------------------------------------------------
class Synapse(ParameterSpace):
    def __init__(self, cell_type, parameters, initial_values, sim_timestep_ms):
        # Superclass
        super(Synapse, self).__init__(cell_type.synapse_mutable_param_map,
                                      cell_type.synapse_immutable_param_map,
                                      parameters, initial_values,
                                      sim_timestep_ms=sim_timestep_ms)
