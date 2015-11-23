# Import modules
import lazyarray as la
import numpy as np

# Import classes
from utils import LazyArrayFloatToFixConverter

# Import functions
from copy import copy, deepcopy

# Create a converter function to convert from float to S1615 format
float_to_s1615_no_copy = LazyArrayFloatToFixConverter(True, 32, 15, False)

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def apply(lazy_params, param_map, size, sim_timestep_us):
    # Build numpy record datatype for neuron region
    # **TODO** this probably doesn't need to be a string:
    # could use np.uint8 style things throughout
    record_datatype = ",".join(zip(*param_map)[1])

    # Build a numpy record array large enough for all neurons
    params = np.empty(size, dtype=(record_datatype))

    # Loop through parameters
    for f, n in zip(params.dtype.names, param_map):
        # If this map entry has a constant value,
        # Write it into field for all neurons
        if len(n) == 2:
            params[f][:] = n[0]
        # Otherwise
        else:
            assert len(n) == 3

            # Transform lazy array, evaluate and write result into parameter row
            params[f] = n[2](lazy_params[n[0]], sim_timestep_us).evaluate()

    return params

def integer(values, sim_timestep_ms):
    vals = deepcopy(values)
    return la.rint(vals)

def integer_time_divide(values, sim_timestep_ms):
    # Copy values and divide by timestep
    scaled_vals = deepcopy(values)
    scaled_vals /= sim_timestep_ms

    # Round and return
    return la.rint(scaled_vals)

def fixed_point(values, sim_timestep_ms):
    vals = deepcopy(values)
    return float_to_s1615_no_copy(vals)

def fixed_point_time_multiply(values, sim_timestep_ms):
    # Copy values and divide by timestep
    scaled_vals = deepcopy(values)
    scaled_vals /= sim_timestep_ms

    # Convert to fixed-point and return
    return float_to_s1615_no_copy(exp_init_vals)

def fixed_point_exp_decay(values, sim_timestep_ms):
    # Copy values and calculate exponential decay
    exp_decay_vals = deepcopy(values)
    exp_decay_vals = la.exp(-sim_timestep_ms / exp_decay_vals)

    # Convert to fixed-point and return
    return float_to_s1615_no_copy(exp_decay_vals)

def fixed_point_exp_init(values, sim_timestep_ms):
    # Copy values and calculate exponential init
    exp_init_vals = deepcopy(values)
    exp_init_vals = 1.0 - la.exp(-sim_timestep_ms / exp_init_vals)
    exp_init_vals *= (values / sim_timestep_ms)

    # Convert to fixed-point and return
    return float_to_s1615_no_copy(exp_init_vals)