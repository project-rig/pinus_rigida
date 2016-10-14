# Import modules
import lazyarray as la
from spinnaker import lazy_param_map
from scipy.stats import norm, expon

# Import classes
from pyNN.random import NativeRNG
from pyNN.errors import InvalidParameterValueError

# Import functions
from six import iteritems

# ----------------------------------------------------------------------------
# NativeRNG
# ----------------------------------------------------------------------------
# Signals that the random numbers will be supplied by RNG running on SpiNNaker
class NativeRNG(NativeRNG):
    # Maps specifying how each distribution type's
    # parameters will be written to SpiNNaker
    _dist_param_maps = {
        "uniform":      [("low",    "i4", lazy_param_map.s32_fixed_point),
                         ("high",   "i4", lazy_param_map.s32_fixed_point)],
        "uniform_int":  [("low",    "i4", lazy_param_map.s32_fixed_point),
                         ("high",   "i4", lazy_param_map.s32_fixed_point)],
        "normal":       [("mu",     "i4", lazy_param_map.s32_fixed_point),
                         ("sigma",  "i4", lazy_param_map.s32_fixed_point)],
        "exponential":  [("beta",   "i4", lazy_param_map.s32_fixed_point)],
        "normal_clipped": [("mu",    "i4", lazy_param_map.s32_fixed_point),
                           ("sigma", "i4", lazy_param_map.s32_fixed_point),
                           ("low",   "i4", lazy_param_map.s32_fixed_point),
                           ("high",  "i4", lazy_param_map.s32_fixed_point)],
        "normal_clipped_to_boundary": [("mu",    "i4", lazy_param_map.s32_fixed_point),
                                       ("sigma", "i4", lazy_param_map.s32_fixed_point),
                                       ("low",   "i4", lazy_param_map.s32_fixed_point),
                                       ("high",  "i4", lazy_param_map.s32_fixed_point)]

    }

    # Functions to estimate the maximum value a distribution will result in
    # **THINK** should this be moved out of NativeRNG
    # for more general estimation of max delays etc

    _dist_estimate_max_value = {
        "uniform":      lambda parameters: parameters["high"],
        "uniform_int":  lambda parameters: parameters["high"],
        "normal":       lambda parameters: parameters["mu"] + parameters["sigma"] *  \
                                           norm.ppf(1-1e-6),
        "normal_clipped": lambda parameters: min(parameters["mu"] + parameters["sigma"] * \
                                                 norm.ppf(1-1e-6), parameters["high"]),
        "normal_clipped_to_boundary": lambda parameters: min(parameters["mu"] + parameters["sigma"] * \
                                                 norm.ppf(1-1e-6), parameters["high"]),
        "exponential":  lambda parameters: parameters["beta"] * expon.ppf(1-1e-6)
    }

    # Functions to check that the distribution parameters are valid.
    # For normal_clipped we also check that the probability of sampling
    # within the specified region is greater than 1e-4

    _dist_check_parameters = {
        "uniform":        lambda parameters: (True, ""),
        "uniform_int":    lambda parameters: (True, ""),
        "normal":         lambda parameters: (parameters["sigma"] > 0, "Expected positive sigma"),
        "normal_clipped": lambda parameters: (parameters["sigma"] > 0 \
                   and norm.cdf((parameters["high"] - parameters["mu"])/parameters["sigma"]) \
                   - norm.cdf((parameters["low"] - parameters["mu"])/parameters["sigma"]) > 1e-4,
                                              "Expected positive sigma and greater than"
                                              " 1e-4 probability of sampling between low and high"),
        "normal_clipped_to_boundary": lambda parameters: (parameters["sigma"] > 0 \
                                      and parameters["high"] > parameters["low"],
                                              "Expected positive sigma and low <= high"),
        "exponential":    lambda parameters: (True, "")
    }

    def __init__(self, host_rng, seed=None):
        # Superclass
        super(NativeRNG, self).__init__(seed)

        # Cache RNG to use on the host
        assert host_rng is not None
        self._host_rng = host_rng

    # ------------------------------------------------------------------------
    # AbstractRNG methods
    # ------------------------------------------------------------------------
    def next(self, n=None, distribution=None, parameters=None, mask_local=None):
        # Draw from host RNG
        return self._host_rng.next(n, distribution, parameters, mask_local)

    # ------------------------------------------------------------------------
    # Internal SpiNNaker methods
    # ------------------------------------------------------------------------
    def _supports_dist(self, distribution):
        return distribution in self._dist_param_maps

    def _estimate_dist_max_value(self, distribution, parameters):
         # Check translation and parameter map exists for this distribution
        if not self._supports_dist(distribution):
            raise NotImplementedError("SpiNNaker native RNG does not support"
                                      "%s distributions" % distribution)
        else:
            return self._dist_estimate_max_value[distribution](parameters)

    def _check_dist_parameters(self, distribution, parameters):
        if not self._supports_dist(distribution):
            raise NotImplementedError("SpiNNaker native RNG does not support"
                                      "%s distributions" % distribution)
        else:
            return self._dist_check_parameters[distribution](parameters)

    def _get_dist_param_map(self, distribution):
        # Check translation and parameter map exists for this distribution
        if not self._supports_dist(distribution):
            raise NotImplementedError("SpiNNaker native RNG does not support"
                                      "%s distributions" % distribution)
        else:
            return self._dist_param_maps[distribution]

    def _get_dist_size(self, distribution):
        # Check translation and parameter map exists for this distribution
        if not self._supports_dist(distribution):
            raise NotImplementedError("SpiNNaker native RNG does not support"
                                      "%s distributions" % distribution)
        else:
            return lazy_param_map.size(self._get_dist_param_map(distribution),
                                       1)

    def _write_dist(self, fp, distribution, parameters, fixed_point):

        parameters_as_expected, err_msg = self._check_dist_parameters(distribution, parameters)
        if not parameters_as_expected:
            raise InvalidParameterValueError(err_msg)

        # Wrap parameters in lazy arrays
        parameters = {name: la.larray(value)
                      for name, value in iteritems(parameters)}

        # Evaluate parameters and write to file
        data = lazy_param_map.apply(
            parameters, self._get_dist_param_map(distribution),
            1, fixed_point=fixed_point)

        fp.write(data.tostring())

    # ------------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------------
    @property
    def parallel_safe(self):
        return self._host_rng.parallel_safe

