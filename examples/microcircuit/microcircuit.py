###################################################
###     	Main script			###        
###################################################

import sys
import numpy as np
from sim_params import simulator_params, system_params
sys.path.append(system_params['backend_path'])
sys.path.append(system_params['pyNN_path'])
from network_params import *
import logging
import pickle
import pyNN
import time
from neo.io import PyNNTextIO
import plotting


# prepare simulation
if simulator == "pynn_spinnaker":
    import pynn_spinnaker as sim

    logger = logging.getLogger("pynn_spinnaker")
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
else:
    exec('import pyNN.%s as sim' % simulator)
#
sim.setup(**simulator_params[simulator])
import network

# create network
start_netw = time.time()
n = network.Network(sim)
n.setup(sim)
end_netw = time.time()
if sim.rank() == 0 :
    print('Creating the network took %g s' % (end_netw - start_netw,))

# simulate
if sim.rank() == 0 :
    print("Simulating...")
start_sim = time.time()
t = sim.run(simulator_params[simulator]['sim_duration'])
end_sim = time.time()
if sim.rank() == 0 :
    print('Simulation took %g s' % (end_sim - start_sim,))

start_writing = time.time()
for layer in n.pops :
    for pop in n.pops[layer] :
        io = PyNNTextIO(filename=system_params['output_path'] \
             + "/spikes_" + layer + '_' + pop + '_' + str(sim.rank()) + ".txt")
        spikes = n.pops[layer][pop].get_data('spikes', gather=False)
        for segment in spikes.segments :
            io.write_segment(segment)
        if record_v :
            io = PyNNTextIO(filename=system_params['output_path'] \
                 + "/vm_" + layer + '_' + pop + '_' + str(sim.rank()) + ".txt")
            vm = n.pops[layer][pop].get_data('v', gather=False)
            for segment in vm.segments :
                try :
                    io.write_segment(segment)
                except AssertionError :
                    pass


end_writing = time.time()
print("Writing data took %g s" % (end_writing - start_writing,))

if create_raster_plot and sim.rank() == 0 :
    # Numbers of neurons from which spikes were recorded
    n_rec = [[0] * n_pops_per_layer] * n_layers
    for layer, i in layers.items() :
        for pop, j in pops.items() :
            if record_fraction:
                n_rec[i][j] = round(N_full[layer][pop] * N_scaling * frac_record_spikes)
            else:
                n_rec[i][j] = n_record
    plotting.show_raster_bars(raster_t_min, raster_t_max, n_rec, frac_to_plot,
                              system_params['output_path'] + '/')

sim.end()
