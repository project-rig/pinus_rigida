import logging
import numpy as np
import pynn_spinnaker as sim

from six import iteritems

logger = logging.getLogger("pynn_spinnaker")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

setup_kwargs = {"spinnaker_hostname": "192.168.1.1",
                "convert_direct_connections": False}

n_stim = 1000
stim_rate = 10.0
n_neurons = 8192
connection_prob = 1.0
duration = 5000
current = 0.7575 # 10Hz
#current = 0.7501 # 5Hz
static = True

profile = False
record_spikes = False

n_synapses = n_neurons * n_stim * connection_prob
print("Number of synapses:%u" % n_synapses)
print("Synaptic event rate:%fHz" % (n_synapses * stim_rate))

sim.setup(timestep=1.0, **setup_kwargs)

pop_stim = sim.Population(n_stim, sim.SpikeSourcePoisson(rate=stim_rate, duration=duration),
                          label="stim")
pop_neurons = sim.Population(n_neurons, sim.IF_curr_exp(tau_refrac=2.0, i_offset=current),
                             label="pop")
if profile:
    pop_neurons.spinnaker_config.num_profile_samples = 1E5

if record_spikes:
    pop_neurons.record("spikes")

if static:
    synapse = sim.StaticSynapse(weight=0.0)
else:
    synapse = sim.STDPMechanism(
        #timing_dependence=sim.Vogels2011Rule(eta=0.005, rho=0.2),
        timing_dependence=sim.SpikePairRule(tau_plus=16.7, tau_minus=33.7, A_plus=0.0, A_minus=0.0),
        weight_dependence=sim.AdditiveWeightDependence(w_min=0.0, w_max=0.0),
        weight=0.0, delay=1.0, dendritic_delay_fraction=1.0)

sim.Projection(pop_stim, pop_neurons, sim.FixedProbabilityConnector(connection_prob),
               synapse, receptor_type="excitatory", label="proj")

sim.run(duration)

if record_spikes:
    pop_neurons_data = pop_neurons.get_data()
    mean_num_out_spikes = np.mean([float(len(s)) for s in pop_neurons_data.segments[0].spiketrains])
    mean_out_rate = mean_num_out_spikes / (duration / 1000.0)
    print("Out rate:%fHz (post spikes per pre:%f)" % (mean_out_rate, mean_out_rate/stim_rate))

if profile:
    print("Neural:")
    n_profiling_data = pop_neurons.get_neural_profile_data()[0][1]
    sim.profiling.print_summary(n_profiling_data, duration, 1.0)

    for i, (t, c) in enumerate(iteritems(pop_neurons.get_synapse_profile_data())):
        print("E synapse type %s:" % str(t))
        sim.profiling.print_summary(c[0][1], duration, 1.0)

# End simulation
sim.end()

