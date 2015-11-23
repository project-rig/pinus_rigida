# Import modules
import functools
import logging
from pyNN.standardmodels import cells
from ..spinnaker import lazy_param_map

# Import functions
from copy import deepcopy
from pyNN.standardmodels import build_translations

logger = logging.getLogger("PyNN")

#-------------------------------------------------------------------
# Neuron type translations
#-------------------------------------------------------------------
# Build translations from PyNN to SpiNNaker neuron model parameters
if_curr_neuron_translations = build_translations(
    ("tau_m",       "tau_m"),
    ("cm",          "r_membrane", "tau_m / cm", ""),
    ("v_rest",      "v_rest"),
    ("v_thresh",    "v_thresh"),
    ("v_reset",     "v_reset"),
    ("tau_refrac",  "tau_refrac"),
    ("i_offset",    "i_offset"),
)

izhikevich_neuron_translations = build_translations(
    ("a",         "a"),
    ("b",         "b"),
    ("c",         "c"),
    ("d",         "d"),
    ("i_offset",  "i_offset"),
)

#-------------------------------------------------------------------
# Synapse type translations
#-------------------------------------------------------------------
# Build translations from PyNN to SpiNNaker synapse model parameters
exp_synapse_translations = build_translations(
    ("tau_syn_E",   "tau_syn_e"),
    ("tau_syn_I",   "tau_syn_i"),
)

#-------------------------------------------------------------------
# Neuron region maps
#------------------------------------------------------------lazy_array_fixed_point-------
# Build maps of where and how parameters need to be written into neuron regions
if_curr_neuron_immutable_param_map = [
    ("v_thresh",    "i4", lazy_param_map.fixed_point),
    ("v_reset",     "i4", lazy_param_map.fixed_point),
    ("v_rest",      "i4", lazy_param_map.fixed_point),
    ("i_offset",    "i4", lazy_param_map.fixed_point),
    ("r_membrane",  "i4", lazy_param_map.fixed_point),
    ("tau_m",       "i4", lazy_param_map.fixed_point_exp_decay),
    ("tau_refrac",  "i4", lazy_param_map.integer_time_divide),
]

if_curr_neuron_mutable_param_map = [
    ("v", "i4", lazy_param_map.fixed_point),
    (0,   "i4"),
]

#-------------------------------------------------------------------
# Synapse shaping region maps
#-------------------------------------------------------------------
exp_synapse_immutable_param_map = [
    ("tau_syn_e", "i4", lazy_param_map.fixed_point_exp_decay),
    ("tau_syn_e", "i4", lazy_param_map.fixed_point_exp_init),
    ("tau_syn_i", "i4", lazy_param_map.fixed_point_exp_decay),
    ("tau_syn_i", "i4", lazy_param_map.fixed_point_exp_init),
]

exp_synapse_mutable_param_map = [
    ("isyn_exc", "i4", lazy_param_map.fixed_point),
    ("isyn_inh", "i4", lazy_param_map.fixed_point),
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