from pyNN.standardmodels import synapses, build_translations
from ..simulator import state
import logging

logger = logging.getLogger("PyNN")


class StaticSynapse(synapses.StaticSynapse):
    __doc__ = synapses.StaticSynapse.__doc__
    translations = build_translations(
        ("weight", "weight"),
        ("delay", "delay"),
    )

    def _get_minimum_delay(self):
        d = state.min_delay
        if d == "auto":
            d = state.dt
        return d

'''
class STDPMechanism(synapses.STDPMechanism):
    __doc__ = synapses.STDPMechanism.__doc__

    base_translations = build_translations(
        ('weight', 'weight'),
        ('delay', 'delay')
    )

    def _get_minimum_delay(self):
        d = state.min_delay
        if d == 'auto':
            d = state.dt
        return d
    

class AdditiveWeightDependence(synapses.AdditiveWeightDependence):
    __doc__ = synapses.AdditiveWeightDependence.__doc__

    translations = build_translations(
        ('w_max',     'w_max'),
        ('w_min',     'w_min'),
        ('A_plus',    'a_plus'),
        ('A_minus',   'a_minus'),
    )


class MultiplicativeWeightDependence(synapses.MultiplicativeWeightDependence):
    __doc__ = synapses.MultiplicativeWeightDependence.__doc__

    translations = build_translations(
        ('w_max',     'wmax'),
        ('w_min',     'wmin'),
        ('A_plus',    'aLTP'),
        ('A_minus',   'aLTD'),
    )

class AdditivePotentiationMultiplicativeDepression(synapses.AdditivePotentiationMultiplicativeDepression):
    __doc__ = synapses.AdditivePotentiationMultiplicativeDepression.__doc__

    translations = build_translations(
        ('w_max',     'wmax'),
        ('w_min',     'wmin'),
        ('A_plus',    'aLTP'),
        ('A_minus',   'aLTD'),
    )

class SpikePairRule(synapses.SpikePairRule):
    __doc__ = synapses.SpikePairRule.__doc__

    translations = build_translations(
        ('tau_plus',  'tauLTP'),
        ('tau_minus', 'tauLTD'),
        ('A_plus',    'aLTP'),
        ('A_minus',   'aLTD'),
    )
'''