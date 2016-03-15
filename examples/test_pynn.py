import itertools
import logging
import math
import matplotlib.pyplot as plt
import numpy as np

from collections import defaultdict
from six import iteritems, iterkeys, itervalues

record_voltages = True
num_neurons = 10
duration = 100
dt = 1.0
nest = False
pinus = True
legacy = False
spinnaker_config = defaultdict(dict)

def simulate(sim, setup_kwargs):
    sim.setup(timestep=dt, **setup_kwargs)
    
    pop_a = sim.Population(num_neurons, sim.IF_curr_exp(i_offset=2.0, tau_refrac=2.0),
                           label="pop_a")
    pop_a.record("spikes")
    #spinnaker_config[pop_a] = { "profile_samples": 2000 }

    if record_voltages:
        pop_a.sample(1).record("v")

    pop_b = sim.Population(num_neurons, sim.IF_curr_exp(tau_refrac=2.0),
                           label="pop_b")
    pop_b.record("spikes")
    #spinnaker_config[pop_b] = { "profile_samples": 2000 }
    
    if record_voltages:
        pop_b.sample(1).record("v")

    # Build list connector that sweeps delay space
    proj = sim.Projection(pop_a, pop_b, sim.OneToOneConnector(),
                          sim.StaticSynapse(weight=2.0, delay=dt),
                          receptor_type="excitatory")

    sim.run(duration)

    pop_a_data = pop_a.get_data()
    pop_b_data = pop_b.get_data()

    # End simulation
    sim.end()

    return pop_a_data, pop_b_data

def simulate_pinus():
    import pynn_spinnaker as sim

    logger = logging.getLogger("pynn_spinnaker")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    setup_kwargs = {
        "spinnaker_hostname": "192.168.1.1",
        "spinnaker_width": 8,
        "spinnaker_height": 8}

    return simulate(sim, setup_kwargs)

def simulate_nest():
    import pyNN.nest as sim
    return simulate(sim, {"spike_precision": "on_grid"})


def plot_spiketrains(axis, segment, **kwargs):
    for spiketrain in segment.spiketrains:
        y = np.ones_like(spiketrain) * spiketrain.annotations["source_index"]
        axis.scatter(spiketrain, y, linewidths=0.0, s=4, **kwargs)

def plot_signal(axis, signal_array, index, **kwargs):
    axis.plot(signal_array.times, signal_array[:, index], **kwargs)

# Run desired simulators
data = {}
if nest:
    data["NEST"] = (simulate_nest(), { "color": "blue" })

if pinus:
    data["SpiNNaker"] = (simulate_pinus(), { "color": "red" })

legacy_kwargs = { "color": "green", "alpha": 0.5 }

figure, axes = plt.subplots(4 if record_voltages else 2, sharex=True)

axes[0].set_title("Population A spikes")
axes[1].set_title("Population B spikes")
axes[0].set_ylabel("Neuron ID")
axes[1].set_ylabel("Neuron ID")

# Loop through all simulator's output data
for l, d in iteritems(data):
    # Loop through recorded populations and plot spike trains
    for i, p in enumerate(d[0]):
        plot_spiketrains(axes[i], p.segments[0], **d[1])

if legacy:
    pop_a_spikes = np.load("pop_a_pacman_spikes.npy")
    pop_b_spikes = np.load("pop_b_pacman_spikes.npy")

    axes[0].scatter(pop_a_spikes[:,1], pop_a_spikes[:,0], linewidths=0.0, s=4, **legacy_kwargs)
    axes[1].scatter(pop_b_spikes[:,1], pop_b_spikes[:,0], linewidths=0.0, s=4, **legacy_kwargs)

if record_voltages:
    axes[2].set_title("Population A membrane voltage")
    axes[3].set_title("Population B membrane voltage")
    axes[2].set_ylabel("Membrane voltage [mV]")
    axes[3].set_ylabel("Membrane voltage [mV]")

    # Loop through all simulator's output data
    for d in itervalues(data):
        # Loop through recorded populations and plot spike trains
        for i, p in enumerate(d[0]):
            plot_signal(axes[2 + i], p.segments[0].analogsignalarrays[0], 0, **d[1])

    if legacy:
        pop_a_voltage = np.load("pop_a_pacman_voltage.npy")
        pop_b_voltage = np.load("pop_b_pacman_voltage.npy")

        axes[2].plot(pop_a_voltage[:,1], pop_a_voltage[:,2], **legacy_kwargs)
        axes[3].plot(pop_b_voltage[:,1], pop_b_voltage[:,2], **legacy_kwargs)

axes[-1].set_xlim((0, duration))

# Build legend
legend_handles = [plt.Line2D([], [], **d[1]) for d in itervalues(data)]
legend_labels = list(iterkeys(data))

if legacy:
    legend_handles.append(plt.Line2D([], [], **legacy_kwargs))
    legend_labels.append("PACMAN")

figure.legend(legend_handles, legend_labels)
plt.show()