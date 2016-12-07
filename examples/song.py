# --------------------------------------------------------------------------
# Song, S., Miller, K. D., & Abbott, L. F. (2000).
# Competitive Hebbian learning through spike-timing-dependent synaptic plasticity.
# Nature Neuroscience, 3(9), 919-26. http://doi.org/10.1038/78829
# --------------------------------------------------------------------------

import itertools
import logging
import matplotlib.pyplot as plt
import numpy as np
from pyNN.random import NumpyRNG, RandomDistribution
from six import iteritems, iterkeys, itervalues

dt = 1.0
num_ex_synapses = 1000
num_neurons = 1
g_max = 0.01
duration = 300000

def simulate(sim, rng, setup_kwargs):
    sim.setup(timestep=dt, **setup_kwargs)

    # Brian was performing synaptic input with ge*(Ee-vr)
    # Ee = 0 so infact Vr is being treated as an input resistance and therefore C = tau_m / v_rest = 10*10^-3 / 60*10^6 = 0.17*10^-9

    additive_neuron = sim.Population(num_neurons,
                                     sim.IF_curr_exp(v_rest=-74.0, v_reset=-60.0, v_thresh=-54.0,
                                                     tau_syn_E=5.0, tau_syn_I=5.0, tau_m=10.0, cm=0.17))
    multiplicative_neuron = sim.Population(num_neurons,
                                           sim.IF_curr_exp(v_rest=-74.0, v_reset=-60.0, v_thresh=-54.0,
                                                           tau_syn_E=5.0, tau_syn_I=5.0, tau_m=10.0, cm=0.17))

    ex_poisson = sim.Population(num_ex_synapses, sim.SpikeSourcePoisson(rate=15.0))

    additive_neuron.record("spikes")
    multiplicative_neuron.record("spikes")

    a_plus = 0.01
    a_minus = 1.05 * a_plus

    # Create weight distribution
    weight_dist = RandomDistribution("uniform", low=0, high=g_max, rng=rng)

    # Plastic Connection between pre_pop and post_pop
    additive_stdp_model = sim.STDPMechanism(
        timing_dependence=sim.SpikePairRule(tau_plus=20.0, tau_minus=20.00,
                                            A_plus=a_plus, A_minus=a_minus),
        weight_dependence=sim.AdditiveWeightDependence(w_min=0.0, w_max=g_max),
        weight=weight_dist, delay=dt, dendritic_delay_fraction=1.0,
    )

    multiplicative_stdp_model = sim.STDPMechanism(
        timing_dependence=sim.SpikePairRule(tau_plus=20.0, tau_minus=20.00,
                                            A_plus=a_plus, A_minus=a_minus),
        weight_dependence=sim.MultiplicativeWeightDependence(w_min=0.0, w_max=g_max),
        weight=weight_dist, delay=dt, dendritic_delay_fraction=1.0,
    )

    additive_proj = sim.Projection(ex_poisson, additive_neuron, sim.AllToAllConnector(),
                                   additive_stdp_model, receptor_type="excitatory")
    multiplicative_proj = sim.Projection(ex_poisson, multiplicative_neuron, sim.AllToAllConnector(),
                                         multiplicative_stdp_model, receptor_type="excitatory")
    sim.run(duration)

    additive_weights = np.asarray(additive_proj.get("weight", format="list", with_address=False))
    multiplicative_weights = np.asarray(multiplicative_proj.get("weight", format="list", with_address=False))
    additive_data = additive_neuron.get_data()
    multiplicative_data = multiplicative_neuron.get_data()

    # End simulation
    sim.end()

    # Return learned weights and data
    return additive_weights, multiplicative_weights, additive_data, multiplicative_data

def simulate_spinnaker():
    import pynn_spinnaker as sim

    logger = logging.getLogger("pynn_spinnaker")
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

    rng = sim.NativeRNG(host_rng=NumpyRNG())

    return simulate(sim, rng, {"max_delay": dt})

def simulate_nest():
    import pyNN.nest as sim
    rng = NumpyRNG()
    return simulate(sim, rng, {"spike_precision": "on_grid"})

# Simulate network
additive_weights, multiplicative_weights, additive_data, multiplicative_data = simulate_spinnaker()

print("Additive mean firing rate %fHz" % (float(len(additive_data.segments[0].spiketrains[0])) / float(duration / 1000)))
print("Multiplicative mean firing rate %fHz" % (float(len(multiplicative_data.segments[0].spiketrains[0])) / float(duration / 1000)))
figure, axes = plt.subplots(1, 2, sharey=True)
axes[0].hist(additive_weights / g_max, 20)
axes[0].set_title("Additive weight dependence")
axes[0].set_xlabel("Normalised weight")
axes[0].set_ylabel("Number of synapses")
axes[0].set_xlim((0.0, 1.0))

axes[1].hist(multiplicative_weights / g_max, 20)
axes[1].set_title("Multiplicative weight dependence")
axes[1].set_xlabel("Normalised weight")
axes[1].set_xlim((0.0, 1.0))
plt.show()