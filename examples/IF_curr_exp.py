
import logging
from pyNN.utility import get_script_args
import matplotlib.pyplot as plt

spinnaker = False
duration = 1000.0

if spinnaker:
    import pynn_spinnaker as sim

    logger = logging.getLogger("pynn_spinnaker")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    setup_kwargs = { "spinnaker_hostname" : "192.168.1.1" }
else:
    import pyNN.nest as sim

    setup_kwargs = {}

sim.setup(timestep=0.1, min_delay=0.1, max_delay=4.0, **setup_kwargs)

ifcell = sim.Population(1, sim.IF_curr_exp(i_offset=0.1, tau_refrac=3.0, v_thresh=-51.0,
                                           tau_syn_E=2.0, tau_syn_I=5.0, v_reset=-70.0))

spike_sourceE = sim.Population(1, sim.SpikeSourcePoisson(rate=20.0, duration=duration), label="spike source E")
spike_sourceI = sim.Population(1, sim.SpikeSourcePoisson(rate=10.0, duration=duration), label="spike source I")

connE = sim.connect(spike_sourceE, ifcell, weight=1.5, receptor_type='excitatory', delay=2.0)
connI = sim.connect(spike_sourceI, ifcell, weight=-1.5, receptor_type='inhibitory', delay=3.0)

ifcell.record("v")

sim.initialize(ifcell, v=-53.2)

sim.run(duration)

data = ifcell.get_data()

sim.end()

def plot_signal(axis, signal_array, index, **kwargs):
    axis.plot(signal_array.times, signal_array[:, index], **kwargs)

figure, axis = plt.subplots()

axis.set_ylabel("Membrane voltage [mV]")
axis.set_xlabel("Time [ms]")
axis.set_xlim((0, duration))

plot_signal(axis, data.segments[0].analogsignalarrays[0], 0, color="red")


plt.show()
