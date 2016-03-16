import itertools
import logging
import matplotlib.pyplot as plt
import numpy as np
from six import iteritems, iterkeys, itervalues

record_voltages = True
profile = False
num_neurons = 100
duration = 200
dt = 1.0
nest = True
pinus = True

def simulate(sim, setup_kwargs):
    sim.setup(timestep=dt, **setup_kwargs)

    #pop_a = sim.Population(num_neurons, sim.SpikeSourcePoisson(rate=10.0, duration=duration),
    #                       label="pop_a")
    pop_a = sim.Population(num_neurons, sim.SpikeSourceArray(spike_times=[10, 20, 30]),
                           label="pop_a")
    if profile:
        pop_a.spinnaker_config.num_profile_samples = 1E5



    #pop_a[4].set(rate=20.0)
    #pop_a.record("spikes")

    pop_b = sim.Population(num_neurons, sim.IF_curr_exp(tau_refrac=2.0),
                           label="pop_b")
    pop_b.record("spikes")

    if record_voltages:
        pop_b.sample(1).record("v")

    proj = sim.Projection(pop_a, pop_b, sim.OneToOneConnector(),
                          sim.StaticSynapse(weight=6.0),
                          receptor_type="excitatory", label="proj")

    sim.run(duration)

    #pop_a_data = pop_a.get_data()
    pop_b_data = pop_b.get_data()

    if profile:
        #print("E neural:")
        #n_profiling_data = pop_a.get_neural_profile_data()[0][1]
        #sim.profiling.print_summary(n_profiling_data, tstop, dt)
        for p, c in iteritems(pop_a.get_current_input_profile_data()):
            print("Direct projection %s:" % p.label)
            sim.profiling.print_summary(c[0][1], duration, dt)

    # End simulation
    sim.end()

    #return pop_a_data, pop_b_data
    return pop_b_data

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

figure, axes = plt.subplots(2 if record_voltages else 1, sharex=True)

spike_axis = axes[0] if record_voltages else axes
spike_axis.set_title("Population A spikes")
#axes[1].set_title("Population B spikes")
spike_axis.set_ylabel("Neuron ID")
#axes[1].set_ylabel("Neuron ID")
spike_axis.set_ylim((0, num_neurons))
#axes[1].set_ylim((0, num_neurons))

# Loop through all simulator's output data
for d in itervalues(data):
    plot_spiketrains(spike_axis, d[0].segments[0], **d[1])

if record_voltages:
    axes[1].set_title("Population B membrane voltage")
    axes[1].set_ylabel("Membrane voltage [mV]")

    for d in itervalues(data):
        plot_signal(axes[1], d[0].segments[0].analogsignalarrays[0], 0, **d[1])

spike_axis.set_xlim((0, duration))

# Build legend
legend_handles = [plt.Line2D([], [], **d[1]) for d in itervalues(data)]
legend_labels = list(iterkeys(data))

figure.legend(legend_handles, legend_labels)
plt.show()