from copy import deepcopy
from pyNN.standardmodels import cells, build_translations
from rig.type_casts import NumpyFloatToFixConverter
from ..simulator import State
import logging
import numpy

logger = logging.getLogger("PyNN")

# Create a converter function to convert from float to S1516 format
float_to_s1516 = NumpyFloatToFixConverter(True, 32, 16)

#-------------------------------------------------------------------
# Neuron type translations
#-------------------------------------------------------------------
# Build translations from PyNN to SpiNNaker neuron model parameters
if_curr_neuron_translations = build_translations(
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
exp_synapse_translations = build_translations(
    ("tau_syn_E",   "exp_tau_syn_e",  "lazyarray.exp(-1.0 / tau_syn_E)",  "-1.0 / log(exp_tau_syn_e)"),
    ("tau_syn_I",   "exp_tau_syn_i",  "lazyarray.exp(-1.0 / tau_syn_I)",  "-1.0 / log(exp_tau_syn_i)"),
)

#-------------------------------------------------------------------
# Neuron region maps
#-------------------------------------------------------------------
# Build maps of where and how parameters need to be written into neuron regions
if_curr_neuron_immutable_param_map = [
    ("v_thresh", "i4", float_to_s1516),
    ("v_reset", "i4", float_to_s1516),
    ("v_rest", "i4", float_to_s1516),
    ("i_offset", "i4", float_to_s1516),
    ("r_membrane", "i4", float_to_s1516),
    ("exp_tau_m", "i4", float_to_s1516),
    ("tau_refrac", "i4", numpy.round),
]

if_curr_neuron_mutable_param_map = [
    ("v", "i4", float_to_s1516),
    (0, "i4"),
]

#-------------------------------------------------------------------
# Synapse shaping region maps
#-------------------------------------------------------------------
exp_synapse_immutable_param_map = [
    ("exp_tau_syn_e", "i4", float_to_s1516),
    ("exp_tau_syn_i", "i4", float_to_s1516),
]

exp_synapse_mutable_param_map = [
    ("isyn_exc", "i4", float_to_s1516),
    ("isyn_inh", "i4", float_to_s1516),
]

#-------------------------------------------------------------------
# Cell types
#-------------------------------------------------------------------
class IF_curr_exp(cells.IF_curr_exp):
    __doc__ = cells.IF_curr_exp.__doc__

    translations = deepcopy(if_curr_neuron_translations)
    translations.update(exp_synapse_translations)
    
    neuron_immutable_param_map = if_curr_neuron_immutable_param_map
    neuron_mutable_param_map = if_curr_neuron_mutable_param_map

    synapse_immutable_param_map = exp_synapse_immutable_param_map
    synapse_mutable_param_map = exp_synapse_mutable_param_map

'''
class IF_cond_exp(cells.IF_cond_exp):
    __doc__ = cells.IF_cond_exp.__doc__

    translations = deepcopy(lif_neuron_translations)
    translations.update(conductance_synapse_translations)
    
    neuron_immutable_param_map = lif_neuron_immutable_param_map
    neuron_mutable_param_map = lif_neuron_mutable_param_map

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
'''