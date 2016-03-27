from pyNN.standardmodels import synapses, build_translations
from ..spinnaker import regions
from ..simulator import state
from ..spinnaker import lazy_param_map
import logging

# Import functions
from functools import partial

logger = logging.getLogger("PyNN")

# ------------------------------------------------------------------------------
# ComparisonMixin
# ------------------------------------------------------------------------------
# Mixin to provide comparison based on a tuple of object properties
class ComparisonMixin(object):
    def __eq__(self, other):
        return self.compatible_comparison == other.compatible_comparison

    def __ne__(self, other):
        return not(self == other)

    def __hash__(self):
        return hash(self.compatible_comparison)

# ------------------------------------------------------------------------------
# ParamComparisonMixin
# ------------------------------------------------------------------------------
# Mixin to provide comparison based on a tuple of object properties
class ParamComparisonMixin(ComparisonMixin):
    @property
    def compatible_comparison(self):
        # Start tuple with class type - various STDP components
        # are likely to have similarly named parameters
        # with simular values so this is important 1st check
        comp = (self.__class__,)

        # Loop through names of parameters which
        # much match for objects to be equal
        for p in self.compatibility_param_names:
            # Extract named parameter lazy array from parameter
            # space and check that it's homogeneous
            param_array = self.parameter_space[p]
            assert param_array.is_homogeneous

            # Set it's shape to 1
            # **NOTE** for homogeneous arrays this is a)free and b)works
            param_array.shape = 1

            # Evaluate and simplify
            # **NOTE** for homogeneous arrays this always returns a scalar
            comp += (param_array.evaluate(simplify=True),)
        return comp

# ------------------------------------------------------------------------------
# StaticSynapse
# ------------------------------------------------------------------------------
class StaticSynapse(synapses.StaticSynapse, ComparisonMixin):
    __doc__ = synapses.StaticSynapse.__doc__
    translations = build_translations(
        ("weight", "weight"),
        ("delay", "delay"),
    )

    # How many post-synaptic neurons per core can a
    # SpiNNaker synapse_processor of this type handle
    max_post_neurons_per_core = 1024

    # Assuming relatively long row length, at what rate can a SpiNNaker
    # synapse_processor of this type process synaptic events (hZ)
    max_synaptic_event_rate = 5E6

    # How many timesteps of delay can DTCM ring-buffer handle
    # **NOTE** only 7 timesteps worth of delay can be handled by
    # 8 element delay buffer - The last element is purely for output
    max_dtcm_delay_slots = 7

    def _get_minimum_delay(self):
        d = state.min_delay
        if d == "auto":
            d = state.dt
        return d

    # Static synapses are always compatible with each other
    @property
    def compatible_comparison(self):
        return (self.__class__,)

# ------------------------------------------------------------------------------
# STDPMechanism
# ------------------------------------------------------------------------------
class STDPMechanism(synapses.STDPMechanism, ComparisonMixin):
    __doc__ = synapses.STDPMechanism.__doc__

    base_translations = build_translations(
        ("weight", "weight"),
        ("delay", "delay")
    )

    # How many post-synaptic neurons per core can a
    # SpiNNaker synapse_processor of this type handle
    max_post_neurons_per_core = 512

    # Assuming relatively long row length, at what rate can a SpiNNaker
    # synapse_processor of this type process synaptic events (hZ)
    max_synaptic_event_rate = 2E6

    plasticity_region_class = regions.Plasticity

    # How many timesteps of delay can DTCM ring-buffer handle
    # **NOTE** only 7 timesteps worth of delay can be handled by
    # 8 element delay buffer - The last element is purely for output
    max_dtcm_delay_slots = 7

    def _get_minimum_delay(self):
        d = state.min_delay
        if d == 'auto':
            d = state.dt
        return d

    # The pre-trace
    @property
    def pre_trace_bytes(self):
        return self.timing_dependence.pre_trace_bytes

    # STDP mechanisms should be compared based on their class, timing
    # dependence (parameters) and weight dependence (parameters)
    @property
    def compatible_comparison(self):
        return (self.__class__, self.timing_dependence,
                self.weight_dependence)

    # The parameter map used to create the plasticity region is just the
    # timing and weight dependence's parameter maps concatenated together
    @property
    def plasticity_param_map(self):
        return (self.timing_dependence.plasticity_param_map +
                self.weight_dependence.plasticity_param_map)

    @property
    def executable_filename(self):
        return (self.__class__.__name__.lower() + "_" +
                self.weight_dependence.__class__.__name__.lower() + "_" +
                self.timing_dependence.__class__.__name__.lower())

# ------------------------------------------------------------------------------
# AdditiveWeightDependence
# ------------------------------------------------------------------------------
class AdditiveWeightDependence(synapses.AdditiveWeightDependence,
                               ParamComparisonMixin):
    __doc__ = synapses.AdditiveWeightDependence.__doc__

    translations = build_translations(
        ("w_max",     "w_max"),
        ("w_min",     "w_min"),
    )

    plasticity_param_map = [
        ("w_min", "i4", lazy_param_map.unsigned_weight_fixed_point),
        ("w_max", "i4", lazy_param_map.unsigned_weight_fixed_point),
        ("a_plus", "i4", lazy_param_map.s2211),
        ("a_minus", "i4", lazy_param_map.s2211),
    ]

    compatibility_param_names =  ("w_max", "w_min")

# ------------------------------------------------------------------------------
# SpikePairRule
# ------------------------------------------------------------------------------
class SpikePairRule(synapses.SpikePairRule, ParamComparisonMixin):
    __doc__ = synapses.SpikePairRule.__doc__

    translations = build_translations(
        ("tau_plus",  "tau_plus"),
        ("tau_minus", "tau_minus"),
        ("A_plus",    "a_plus"),
        ("A_minus",   "a_minus"),
    )

    plasticity_param_map = [
        ("tau_plus", "256i2", partial(lazy_param_map.s411_exp_decay_lut,
                                      num_entries=256, time_shift=0)),
        ("tau_minus", "256i2", partial(lazy_param_map.s411_exp_decay_lut,
                                       num_entries=256, time_shift=0)),
    ]

    compatibility_param_names = ("tau_plus", "tau_minus", "A_plus", "A_minus")

    # How many byte does this
    pre_trace_bytes = 2