# Import modules
import lazyarray as la
from spinnaker import lazy_param_map

# Import classes
from pyNN.random import NativeRNG

# Import functions
from six import iteritems

# ----------------------------------------------------------------------------
# NativeRNG
# ----------------------------------------------------------------------------
class NativeRNG(NativeRNG):
    """
    Signals that the random numbers will be supplied by RNG running on SpiNNaker
    """
    # Maps specifying how each distribution type's
    # parameters will be written to SpiNNaker
    param_maps = {
        "uniform":      [("low",    "i4", lazy_param_map.s32_fixed_point),
                         ("high",   "i4", lazy_param_map.s32_fixed_point)],
        "uniform":      [("low",    "i4", lazy_param_map.s32_fixed_point),
                         ("high",   "i4", lazy_param_map.s32_fixed_point)],
    }


    def next(self, n=None, distribution=None, parameters=None, mask_local=None):
        raise NotImplementedError("Parameters chosen using SpiNNaker native"
                                  "RNG can only be evaluated on SpiNNaker")

    # Internal SpiNNaker methods
    def _write_distribution(self, distribution, parameters, fixed_point):
        # Check translation and parameter map exists for this distribution
        if (distribution not in self.param_maps):
            raise NotImplementedError("SpiNNaker native RNG does not support"
                                      "%s distributions" % distribution)

        # Wrap parameters in lazy arrays
        parameters = {name: la.larray(value)
                      for name, value in iteritems(parameters)}

        # Evaluate parameters
        spinnaker_params = lazy_param_map.apply(parameters,
                                                self.param_maps[distribution],
                                                1, fixed_point=fixed_point)
        print spinnaker_params


