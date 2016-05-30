# Import modules
import itertools
from pynn_spinnaker.spinnaker import lazy_param_map
import numpy as np
import pytest

# Import classes
from pyNN.parameters import ParameterSpace

# Import functions
from six import iterkeys

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _test(params, size, data_type, mapping_func, correct_value_func):
    # Create parameter space
    param_space = ParameterSpace(params, shape=(size,))

    # Build param map applying mapping function to all parameters
    param_map = [(param_name, data_type, mapping_func)
                 for param_name in iterkeys(params)]

    # Apply map
    mapped_params = lazy_param_map.apply(param_space, param_map, size)

    # Extract parameter names
    param_names = (mapped_params.dtype.names
                   if mapped_params.dtype.names is not None
                   else (slice(None, None, None),))

    # Loop through mapped parameters and the parameter map
    for n, p in zip(param_names, param_map):
        correct_value = correct_value_func(params[p[0]])
        assert np.all(mapped_params[n] == correct_value)

def _test_exception(params, size, data_type, mapping_func, correct_value_func,
                expected_exception):
    if expected_exception is not None:
        with pytest.raises(expected_exception):
            _test(params, size, data_type, mapping_func, correct_value_func)
    else:
        _test(params, size, data_type, mapping_func, correct_value_func)

# ----------------------------------------------------------------------------
# Standard parameters
# ----------------------------------------------------------------------------
scalars = [{"a": 0.5}, {"a": 27.0, "b": 0.5, "c": 0.2}]

# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("params", scalars)
@pytest.mark.parametrize("size", [1, 10])
def test_integer_homogeneous(params, size):
    _test(params, size, "i4", lazy_param_map.integer,
          lambda p: np.round(p).astype(int))

@pytest.mark.parametrize("params, size, value_error",
                         [({"a": np.arange(10.0)}, 10, False),
                          ({"a": np.arange(10.0), "b": np.arange(10.0, 20.0), "c": np.arange(20.0, 30.0)}, 10, False),
                          ({"a": [0.5],  "b": [0.0], "c": [122.0]}, 1, False),
                          ({"a": np.arange(10.0)}, 12, True)])
def test_integer_array(params, size, value_error):
    _test_exception(params, size, "i4", lazy_param_map.integer,
                    lambda p: np.round(p).astype(int),
                    ValueError if value_error else None)

@pytest.mark.parametrize("params", scalars)
@pytest.mark.parametrize("size", [1, 10])
def test_s1615_homogeneous(params, size):
    _test(params, size, "i4", lazy_param_map.s1615,
          lambda p: np.round(p * (2.0 ** 15)).astype(int))

'''
integer
integer_time_divide
s1615
s2211
u32_weight_fixed_point(values, weight_fixed_point, **kwargs):
s32_weight_fixed_point(values, weight_fixed_point, **kwargs):
s1615_time_multiply = partial(time_multiply, float_to_fixed=float_to_s1615_no_copy)
s1615_exp_decay = partial(exp_decay, float_to_fixed=float_to_s1615_no_copy)
u032_exp_decay = partial(exp_decay, float_to_fixed=float_to_u032_no_copy)
s1615_exp_init = partial(exp_init, float_to_fixed=float_to_s1615_no_copy)
s1615_rate_isi = partial(rate_isi, float_to_fixed=float_to_s1615_no_copy)
u032_rate_exp_minus_lambda = partial(rate_exp_minus_lambda, float_to_fixed=float_to_u032_no_copy)
s411_exp_decay_lut = partial(exp_decay_lut, float_to_fixed=float_to_s411_no_copy)
'''
