# Import modules
import lazyarray as la
from spinnaker import lazy_param_map
import numpy as np

# Import classes
from pyNN.random import NativeRNG

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
        "uniform":      [("low",  "i4", lazy_param_map.s32_fixed_point_scale_abs),
                         ("high", "i4", lazy_param_map.s32_fixed_point_scale_abs)],
        "uniform_int":  [("low"   "i4", lazy_param_map.s32_fixed_point_scale_abs),
                         ("high", "i4", lazy_param_map.s32_fixed_point_scale_abs)],
    }

    # Functions to estimate the maximum value a distribution will result in
    # **THINK** should this be moved out of NativeRNG
    # for more general estimation of max delays etc
    _dist_estimate_max_value = {
        "uniform":      lambda parameters: parameters["high"],
        "uniform_int":  lambda parameters: parameters["high"]
    }

    def __init__(self, host_rng, seed=None):
        # Superclass
        super(NativeRNG, self).__init__(seed)

        # Cache RNG to use on the host
        assert host_rng is not None
        self._host_rng = host_rng

        # Generate four word base seed for SpiNNaker RNGs
        self.SeedWords = 4
        self.base_seed = np.random.RandomState(seed=seed).randint(0x7FFFFFFF,
                                          size=self.SeedWords).astype(np.uint32)

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

    def _write_dist(self, fp, distribution, parameters, fixed_point, scale, absolute):
        # Wrap parameters in lazy arrays
        parameters = {name: la.larray(value)
                      for name, value in iteritems(parameters)}

        # Evaluate parameters and write to file
        data = lazy_param_map.apply(
            parameters, self._get_dist_param_map(distribution),
            1, fixed_point=fixed_point, scale=scale, absolute=absolute)
        fp.write(data.tostring())

    # ------------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------------
    @property
    def parallel_safe(self):
        return self._host_rng.parallel_safe

