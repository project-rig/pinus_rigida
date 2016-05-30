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
# BaseTestMapping
# ----------------------------------------------------------------------------
class BaseTestMapping(object):
    # ----------------------------------------------------------------------------
    # Standard parameters
    # ----------------------------------------------------------------------------
    test_scalars = [{"a": 0.5}, {"a": 27.0, "b": 0.5, "c": 0.2}]
    test_arrays = [({"a": np.arange(10.0)}, 10),
                   ({"a": np.arange(10.0), "b": np.arange(10.0, 20.0), "c": np.arange(20.0, 30.0)}, 10),
                   ({"a": [0.5],  "b": [0.0], "c": [122.0]}, 1)]
    test_kwargs = [{}]

    # ----------------------------------------------------------------------------
    # Test methods
    # ----------------------------------------------------------------------------
    @pytest.mark.parametrize("params", test_scalars)
    @pytest.mark.parametrize("size", [1, 10])
    @pytest.mark.parametrize("kwargs", test_kwargs)
    def test_homogeneous(self, params, size, kwargs):
        self._test(params, size, kwargs)

    @pytest.mark.parametrize("params, size", test_arrays)
    @pytest.mark.parametrize("kwargs", test_kwargs)
    def test_array(self, params, size, kwargs):
        self._test(params, size, kwargs)

    @pytest.mark.parametrize("params, size",
                            [(a[0], a[1] + 6) for a in test_arrays])
    @pytest.mark.parametrize("kwargs", test_kwargs)
    def test_array_bad_length(self, params, size, kwargs):
        with pytest.raises(ValueError):
            self._test(params, size, kwargs)

    # ----------------------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------------------
    def _test(self, params, size, kwargs):
        # Create parameter space
        param_space = ParameterSpace(params, shape=(size,))

        # Build param map applying mapping function to all parameters
        param_map = [(param_name, self.data_type, self.mapping_func)
                    for param_name in iterkeys(params)]

        # Apply map
        mapped_params = lazy_param_map.apply(param_space, param_map,
                                             size, **kwargs)

        # Extract parameter names
        param_names = (mapped_params.dtype.names
                    if mapped_params.dtype.names is not None
                    else (slice(None, None, None),))

        # Loop through mapped parameters and the parameter map
        for n, p in zip(param_names, param_map):
            correct_value = self.correct_value_func(params[p[0]], **kwargs)
            assert np.all(mapped_params[n] == correct_value)


# ----------------------------------------------------------------------------
# TestInteger
# ----------------------------------------------------------------------------
class TestInteger(BaseTestMapping):
    mapping_func = staticmethod(lazy_param_map.integer)
    data_type = "i4"

    def correct_value_func(self, p):
        return np.round(p).astype(int)

# ----------------------------------------------------------------------------
# TestIntegerTimeDivide
# ----------------------------------------------------------------------------
'''
class TestIntegerTimeDivide(BaseTestMapping):
    mapping_func = staticmethod(lazy_param_map.integer_time_divide)
    data_type = "i4"
    test_kwargs = [{"sim_timestep_ms": 1.0}, {"sim_timestep_ms": 0.1}]

    def correct_value_func(self, p, sim_timestep_ms):
        return np.round(numpy.divide(p, sim_timestep_ms)).astype(int)
'''
# ----------------------------------------------------------------------------
# TestS1615
# ----------------------------------------------------------------------------
class TestS1615(BaseTestMapping):
    mapping_func = staticmethod(lazy_param_map.s1615)
    data_type = "i4"

    def correct_value_func(self, p):
        return np.round(np.multiply(p, 2.0 ** 15)).astype(int)

# ----------------------------------------------------------------------------
# TestS2211
# ----------------------------------------------------------------------------
class TestS2211(BaseTestMapping):
    mapping_func = staticmethod(lazy_param_map.s2211)
    data_type = "i4"

    def correct_value_func(self, p):
        return np.round(np.multiply(p, 2.0 ** 11)).astype(int)

'''
integer_time_divide

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
