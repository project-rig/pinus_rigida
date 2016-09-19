"""
docstring missing
"""

from pyNN.random import NativeRNG


class NativeRNG(NativeRNG):
    """
    Signals that the random numbers will be supplied by RNG running on SpiNNaker
    """
    translations = {
        'uniform':        {'low': 'low', 'high': 'high'},
        'uniform_int':    {'low': 'low', 'high': 'high'},
    }

    def next(self, n=None, distribution=None, parameters=None, mask_local=None):
        raise NotImplementedError("Parameters chosen using SpiNNaker native"
                                  "RNG can only be evaluated on SpiNNaker")
