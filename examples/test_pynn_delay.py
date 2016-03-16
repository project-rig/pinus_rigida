import itertools
import logging
import math
import matplotlib.pyplot as plt
import numpy as np

from collections import defaultdict
from six import iterkeys, itervalues

num_neurons = 100
duration = 100
dt = 0.1
nest = False
pinus = True
spinnaker_config = defaultdict(dict)

def simulate(sim, setup_kwargs):
    sim.setup(timestep=dt, **setup_kwargs)

    pop_a = sim.Population(1, sim.SpikeSourceArray(spike_times=[1, 50]),
                           label="pop_a")
    #pop_a = sim.Population(1, sim.IF_curr_exp(i_offset=2.0, tau_refrac=20.0),
    #                       label="pop_a")
    pop_a.record("spikes")

    pop_b = sim.Population(num_neurons, sim.IF_curr_exp(tau_refrac=2.0),
                           label="pop_b")
    pop_b.record("spikes")


    # Build list connector that sweeps delay space
    connections = [(0, i, 6.0, dt + i) for i in range(num_neurons)]
    proj = sim.Projection(pop_a, pop_b, sim.FromListConnector(connections),
                          sim.StaticSynapse(),
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
        "spinnaker_height": 8,
        "stop_on_spinnaker": True}

    return simulate(sim, setup_kwargs)

def simulate_nest():
    import pyNN.nest as sim
    return simulate(sim, {})


def plot_spiketrains(axis, segment, **kwargs):
    for spiketrain in segment.spiketrains:
        y = np.ones_like(spiketrain) * spiketrain.annotations["source_index"]
        axis.scatter(spiketrain, y, linewidths=0.0, s=4, **kwargs)
# Run desired simulators
data = {}
if nest:
    data["NEST"] = (simulate_nest(), { "color": "blue" })

if pinus:
    data["SpiNNaker"] = (simulate_pinus(), { "color": "red" })

figure, axes = plt.subplots(2, sharex=True)

axes[0].set_title("Population A spikes")
axes[1].set_title("Population B spikes")
axes[0].set_ylabel("Neuron ID")
axes[1].set_ylabel("Neuron ID")

# Loop through all simulator's output data
for d in itervalues(data):
    # Loop through recorded populations and plot spike trains
    for i, p in enumerate(d[0]):
        plot_spiketrains(axes[i], p.segments[0], **d[1])

axes[-1].set_xlim((0, duration))

# Build legend
legend_handles = [plt.Line2D([], [], **d[1]) for d in itervalues(data)]
legend_labels = list(iterkeys(data))

figure.legend(legend_handles, legend_labels)
plt.show()