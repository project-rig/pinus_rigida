# Import modules
import lazyarray as la
import numpy as np

# Import classes
from utils import LazyArrayFloatToFixConverter

# Import functions
from copy import deepcopy

# Create a converter function to convert from float to S1615 format
float_to_s1615_no_copy = LazyArrayFloatToFixConverter(True, 32, 15, False)
float_to_s2211_no_copy = LazyArrayFloatToFixConverter(True, 32, 11, False)
float_to_u032_no_copy = LazyArrayFloatToFixConverter(False, 32, 32, False)
float_to_s411_no_copy = LazyArrayFloatToFixConverter(True, 16, 11, False)

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------
def _build_dtype(param_map):
    # Build numpy record datatype for neuron region
    # **TODO** this probably doesn't need to be a string:
    # could use np.uint8 style things throughout
    return np.dtype(",".join(zip(*param_map)[1]))

def size(param_map, size):
    return _build_dtype(param_map).itemsize * size

def apply(lazy_params, param_map, size, **kwargs):
    # Build a numpy record array large enough for all neurons
    params = np.empty(size, dtype=_build_dtype(param_map))

    # Loop through parameters
    for field_name, param in zip(params.dtype.names, param_map):
        # If this map entry has a constant value,
        # Write it into field for all neurons
        if len(param) == 2:
            param_value, _ = param
            params[field_name][:] = param_value
        # Otherwise, apply lazy transformation and evaluate
        else:
            param_name, _, param_mapping = param
            params[field_name] =\
                param_mapping(lazy_params[param_name], **kwargs).evaluate()

    return params


def apply_indices(lazy_params, param_map, indices, **kwargs):
    # Build a numpy record array large enough for all neurons
    params = np.empty(len(indices), dtype=_build_dtype(param_map))

    # Loop through parameters
    for field_name, param in zip(params.dtype.names, param_map):
        # If this map entry has a constant value,
        # Write it into field for all neurons
        if len(param) == 2:
            param_value, _ = param
            if param_value is None:
                params[field_name] = indices
            else:
                params[field_name][:] = param_value
        # Otherwise, apply lazy transformation and evaluate slice
        elif len(indices) > 0:
            param_name, _, param_mapping = param
            params[field_name] = param_mapping(lazy_params[param_name],
                                               **kwargs)[indices]

    return params


def integer(values, **kwargs):
    vals = deepcopy(values)
    return la.rint(vals)


def integer_time_divide(values, sim_timestep_ms, **kwargs):
    # Copy values and divide by timestep
    scaled_vals = deepcopy(values)
    scaled_vals /= sim_timestep_ms

    # Round and return
    return la.rint(scaled_vals)


def s1615(values, **kwargs):
    return float_to_s1615_no_copy(deepcopy(values))

def s2211(values, **kwargs):
    return float_to_s2211_no_copy(deepcopy(values))

def unsigned_weight_fixed_point(values, weight_fixed_point, **kwargs):
    float_to_weight_no_copy = LazyArrayFloatToFixConverter(
        False, 16, weight_fixed_point, False)
    return float_to_weight_no_copy(deepcopy(values))

def s1615_time_multiply(values, sim_timestep_ms, **kwargs):
    # Copy values and divide by timestep
    scaled_vals = deepcopy(values)
    scaled_vals /= sim_timestep_ms

    # Convert to fixed-point and return
    return float_to_s1615_no_copy(scaled_vals)


def s1615_exp_decay(values, sim_timestep_ms, **kwargs):
    # Copy values and calculate exponential decay
    exp_decay_vals = deepcopy(values)
    exp_decay_vals = la.exp(-sim_timestep_ms / exp_decay_vals)

    # Convert to fixed-point and return
    return float_to_s1615_no_copy(exp_decay_vals)


def s1615_exp_init(values, sim_timestep_ms, **kwargs):
    # Copy values and calculate exponential init
    exp_init_vals = deepcopy(values)
    exp_init_vals = 1.0 - la.exp(-sim_timestep_ms / exp_init_vals)
    exp_init_vals *= (values / sim_timestep_ms)

    # Convert to fixed-point and return
    return float_to_s1615_no_copy(exp_init_vals)


def s1615_rate_isi(values, sim_timestep_ms, **kwargs):
    # Copy values and convert rates to isis
    isi_vals = deepcopy(values)
    isi_vals = 1000.0 / (isi_vals * sim_timestep_ms)

    # Convert to fixed-point and return
    return float_to_s1615_no_copy(isi_vals)


def u032_rate_exp_minus_lambda(values, sim_timestep_ms, **kwargs):
    # Copy values and convert to spikes per-tick
    lambda_vals = deepcopy(values)
    lambda_vals = (lambda_vals * sim_timestep_ms) / 1000.0

    # Calculate exponential
    lambda_vals = la.exp(-1.0 / lambda_vals)

    # Convert to fixed point and return
    return float_to_u032_no_copy(lambda_vals)

def s411_exp_decay_lut(values, num_entries, time_shift, sim_timestep_ms,
                       **kwargs):
    # Determine the time step of the LUT in milliseconds
    timestep_ms = sim_timestep_ms * float(2 ** time_shift)

    # Build a lazy array of times to calculate decay values for
    time_ms = la.larray(
        np.arange(0.0, -timestep_ms * float(num_entries), -timestep_ms))

    # Calculate exponential decay
    values.shape = time_ms.shape
    decay_vals = la.exp(time_ms / values)
    return float_to_s411_no_copy(decay_vals)