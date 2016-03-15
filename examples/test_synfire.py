import itertools
import logging
import matplotlib.pyplot as plt
import numpy as np

from collections import defaultdict
from six import iterkeys, itervalues

num_neurons = 1000
duration = 1000
nest = False
pinus = True

spinnaker_config = defaultdict(dict)

def simulate(sim, setup_kwargs):
    sim.setup(timestep=1.0, **setup_kwargs)

    weight = 6.0

    stim = sim.Population(2, sim.SpikeSourceArray(spike_times=[1]), label="stim")
    pop = sim.Population(num_neurons, sim.IF_curr_exp(tau_refrac=2.0), label="pop")
    #pop[0].i_offset=2.0
    pop.record("spikes")
    #spinnaker_config[pop_a] = { "profile_samples": 2000 }

    pop_conn_list = [(n, (n + 2) % num_neurons, weight, 1.0) for n in range(num_neurons)]
    sim.Projection(pop, pop, sim.FromListConnector(pop_conn_list),
                   sim.StaticSynapse(weight=weight, delay=1.0),
                   receptor_type="excitatory")

    stim_conn_list = [(0, 0, weight, 1.0),
                      (1, 1, weight, 1.0)]
    sim.Projection(stim, pop, sim.FromListConnector(stim_conn_list),
                   sim.StaticSynapse(weight=weight, delay=1.0),
                   receptor_type="excitatory")

    sim.run(duration)

    pop = pop.get_data()

    # End simulation
    sim.end()

    return pop

def simulate_pinus():
    import pynn_spinnaker as sim

    logger = logging.getLogger("pynn_spinnaker")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    setup_kwargs = {
        "spinnaker_hostname": "192.168.1.1",
        "spinnaker_width": 8,
        "spinnaker_height": 8,
        "config": spinnaker_config}

    return simulate(sim, setup_kwargs)

def simulate_nest():
    import pyNN.nest as sim
    return simulate(sim, {})


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

figure, axis = plt.subplots(sharex=True)

axis.set_ylabel("Neuron ID")

# Loop through all simulator's output data
for d in itervalues(data):
    plot_spiketrains(axis, d[0].segments[0], **d[1])

axis.set_xlim((0, duration))

# Build legend
legend_handles = [plt.Line2D([], [], **d[1]) for d in itervalues(data)]
legend_labels = list(iterkeys(data))
figure.legend(legend_handles, legend_labels)
plt.show()