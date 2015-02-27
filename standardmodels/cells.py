from copy import deepcopy
from pyNN.standardmodels import cells, build_translations
from rig.type_casts import NumpyFloatToFixConverter
from ..simulator import State
import logging
import numpy

logger = logging.getLogger("PyNN")

#-------------------------------------------------------------------
# Neuron type translations
#-------------------------------------------------------------------
# Build translations from PyNN to SpiNNaker neuron model parameters
lif_neuron_translations = build_translations(
    ("tau_m",       "exp_tau_m",  "lazyarray.exp(-1.0 / tau_m)",  "-1.0 / log(exp_tau_m)"),
    ("cm",          "r_membrane", "tau_m / cm",         ""),
    ("v_rest",      "v_rest"),
    ("v_thresh",    "v_thresh"),
    ("v_reset",     "v_reset"),
    ("tau_refrac",  "tau_refrac",   10.0),  # **NOTE** this is in units of 100uS 
    ("i_offset",    "i_offset"),  # **TODO** scale relative to timestep
)
izhikevich_neuron_translations = build_translations(
    ("a",         "a"),
    ("b",         "b"),
    ("c",         "c"),
    ("d",         "d"),
    ("i_offset",  "i_offset"),  # **TODO** scale relative to timestep
)

#-------------------------------------------------------------------
# Synapse type translations
#-------------------------------------------------------------------
# Build translations from PyNN to SpiNNaker synapse model parameters
current_synapse_translations = build_translations(
    ("tau_syn_E",   "tau_syn_e"),
    ("tau_syn_I",   "tau_syn_i"),
)

conductance_synapse_translations = build_translations(
    ("tau_syn_E",   "tau_syn_e"),
    ("tau_syn_I",   "tau_syn_i"),
    ("e_rev_E",     "e_rev_e"),
    ("e_rev_I",     "e_rev_i"),
)

#-------------------------------------------------------------------
# Neuron region maps
#-------------------------------------------------------------------
# Build maps of where and how parameters need to be written into neuron regions

# Create a converter function to convert from float to S1615 format
float_to_s1615 = NumpyFloatToFixConverter(True, 32, 15)

lif_neuron_region_map = [
    ("v_thresh", "i4", float_to_s1615),
    ("v_reset", "i4", float_to_s1615),
    ("v_rest", "i4", float_to_s1615),     # **TODO** v_init is more cunning than this
    ("r_membrane", "i4", float_to_s1615),
    ("v_rest", "i4", float_to_s1615),     # **TODO** initializing state variables is more cunning than this
    ("i_offset", "i4", float_to_s1615),
    ("exp_tau_m", "i4", float_to_s1615),
    (0, "i4"),                            # **NOTE** not using ODE solver
    ("tau_refrac", "i4", numpy.round),
]

#-------------------------------------------------------------------
# Cell types
#-------------------------------------------------------------------
class IF_curr_exp(cells.IF_curr_exp):
    __doc__ = cells.IF_curr_exp.__doc__

    translations = deepcopy(lif_neuron_translations)
    translations.update(current_synapse_translations)
    
    neuron_region_map = lif_neuron_region_map

class IF_cond_exp(cells.IF_cond_exp):
    __doc__ = cells.IF_cond_exp.__doc__

    translations = deepcopy(lif_neuron_translations)
    translations.update(conductance_synapse_translations)
    
    neuron_region_map = lif_neuron_region_map

class Izhikevich(cells.Izhikevich):
    __doc__ = cells.Izhikevich.__doc__
    
    translations = deepcopy(izhikevich_neuron_translations)
    translations.update(current_synapse_translations)

class SpikeSourcePoisson(cells.SpikeSourcePoisson):
    __doc__ = cells.SpikeSourcePoisson.__doc__

    translations = build_translations(
        ('start',    'START'),
        ('rate',     'INTERVAL',  "1000.0/rate",  "1000.0/INTERVAL"),
        ('duration', 'DURATION'),
    )

class SpikeSourceArray(cells.SpikeSourceArray):
    __doc__ = cells.SpikeSourceArray.__doc__

    translations = build_translations(
        ('spike_times', 'SPIKE_TIMES'),
    )
