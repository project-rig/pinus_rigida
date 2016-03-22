#############################################################
#
# A PyNN Sudoku model
# Steve Furber, November 2015
#
#############################################################

import pynn_spinnaker as p
#import pyNN.nest as p

from   itertools import product
import logging
import pylab
import numpy
from   pyNN.random import RandomDistribution

logger = logging.getLogger("pynn_spinnaker")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

setup_kwargs = {"spinnaker_hostname": "192.168.1.1"}

run_time  = 30000       # ms
fact      = 2.5         # number of neurons per digit/10
init_skew = 200.0       # ms - skew between successive input applications

p.setup(timestep=1.0, **setup_kwargs)
n_cell = int(90*fact)   # total number of neurons in a cell
n_stim = 30             # number of neurons in each stimulation (initialising) source
n_N    = n_cell/9       # number of neurons per value in cell

#global distributions & parameters
weight_cell = RandomDistribution("uniform", low=-0.2/fact, high=-0.0/fact)  # -0.2, 0.0
weight_stim = RandomDistribution("uniform", low=0.0, high=0.1)              # 0.0, 0.1
dur_nois    = RandomDistribution("uniform", low=25000.0, high=30000.0)      # 25000, 30000
weight_nois = 1.0                                                           # 1.0
delay       = 2.0                                                           # 2.0

# Easy problem:
"""
"""
# Hard problem:

init = [[2,0,0,0,0,6,0,3,0],        # initialise non-zeros
        [4,8,0,0,1,9,0,0,0],        # NB use as init[8-y][x] -> cell[x][y]
        [0,0,7,0,2,0,9,0,0],
        [0,0,0,3,0,0,0,9,0],
        [7,0,8,0,0,0,1,0,5],
        [0,4,0,0,0,7,0,0,0],
        [0,0,4,0,9,0,6,0,0],
        [0,0,0,6,4,0,0,1,9],
        [0,5,0,1,0,0,0,0,8]]

corr = [[2,9,1,8,7,6,5,3,4],        # solution for reference
        [4,8,3,5,1,9,2,7,6],        # NB use as corr[8-y][x] -> cell[x][y]
        [5,6,7,4,2,3,9,8,1],
        [6,2,5,3,8,1,4,9,7],
        [7,3,8,9,6,4,1,2,5],
        [1,4,9,2,5,7,8,6,3],
        [3,1,4,7,9,8,6,5,2],
        [8,7,2,6,4,5,3,1,9],
        [9,5,6,1,3,2,7,4,8]]

"""
# Diabolical problem:

init = [[0,0,1,0,0,8,0,7,3],        # initialise non-zeros
        [0,0,5,6,0,0,0,0,1],        # NB use as init[8-y][x] -> cell[x][y]
        [7,0,0,0,0,1,0,0,0],
        [0,9,0,8,1,0,0,0,0],
        [5,3,0,0,0,0,0,4,6],
        [0,0,0,0,6,5,0,3,0],
        [0,0,0,1,0,0,0,0,4],
        [8,0,0,0,0,9,3,0,0],
        [9,4,0,5,0,0,7,0,0]]

corr = init

# Dream problem - no input!
"""

# Dream problem - no input!
"""
init = [[0 for x in range(9)] for y in range(9)]
corr = init
"""
#
# set up the 9x9 cell array populations
#

cell_params_lif = { 'cm':         0.25, # nF    membrane capacitance
                    'i_offset':   0.3,  # nA    bias current
                    'tau_m':     20.0,  # ms    membrane time constant
                    'tau_refrac': 2.0,  # ms    refractory period
                    'tau_syn_E':  5.0,  # ms    excitatory synapse time constant
                    'tau_syn_I':  5.0,  # ms    inhibitory synapse time constant
                    'v_reset':  -70.0,  # mV    reset membrane potential
                    'v_rest':   -65.0,  # mV    rest membrane potential
                    'v_thresh': -50.0   # mV    firing threshold voltage
                    }

print("Creating populations")
cell = [[p.Population(n_cell, p.IF_curr_exp(**cell_params_lif), label="Cell"+str(x+1)+str(y+1)) for x in range(9)] for y in range (9)]

#
# add a noise source to each cell
#

nois = [[p.Population(n_cell, p.SpikeSourcePoisson(rate=20.0, start=0.0, duration=dur_nois),
                      label="Nois"+str(x+1)+str(y+1)) for x in range(9)] for y in range (9)]

print("Creating noise projections")
syn_noise = p.StaticSynapse(weight=weight_nois)
for x, y in product(range(9), repeat=2):
    conn_nois        = p.OneToOneConnector(weight_nois)

    p.Projection(nois[x][y], cell[x][y], conn_nois, syn_noise, receptor_type="excitatory")  # connect noise neurons one-to-one to cell neurons

#
# set up the cell internal inhibitory connections    numpy_spikes = numpy_spikes[numpy.lexsort((spike_times, neuron_ids))]
#
print("Creating cell projections")
syn_static = p.StaticSynapse()
for x, y in product(range(9), repeat=2):
    connections_cell = [(i, j, 0.0 if i//n_N == j//n_N else weight_cell.next(), delay) for i in range(n_cell) for j in range(n_cell)]
    conn_cell        = p.FromListConnector(connections_cell)

    p.Projection(cell[x][y], cell[x][y], conn_cell, syn_static, receptor_type="inhibitory")  # full constant matrix of weight_cell apart from n_N squares on diagonal

#
# set up the inter-cell inhibitory connections
#
print("Creating inter-cell projections")
def interCell(synapse, x, y, r, c):
    "Inhibit same number: connections are n_N squares on diagonal of weight_cell() from cell[x][y] to cell[r][c]"
    connections_intC = []
    for i in range(n_cell):
        for j in range(n_N*(i//n_N), n_N*(i//n_N+1)): connections_intC.append((i, j, weight_cell.next(), delay))
    conn_intC = p.FromListConnector(connections_intC)

    p.Projection(cell[x][y], cell[r][c], conn_intC, synapse, receptor_type="inhibitory")
    return

for x, y in product(range(9), repeat=2):
    for r in range(9):
        if r != x: interCell(syn_static, x, y, r, y)                   # by row...
    for c in range(9):
        if c != y: interCell(syn_static, x, y, x, c)                   # by column...
    for r in range(3*(x//3),3*(x//3+1)):
        for c in range(3*(y//3),3*(y//3+1)):
            if r != x and c != y: interCell(syn_static, x, y, r, c)    # & by square

#
# set up & connect the initial (stimulation) conditions
#

s    = 0
stim = []
syn_stim  = p.StaticSynapse()
for x, y in product(range(9), repeat=2):
    if init[8-y][x] != 0:
        connections_stim = []
        for i in range(n_stim):
            for j in range(n_N*(init[8-y][x]-1), n_N*init[8-y][x]):
                connections_stim.append((i, j, weight_stim.next(), delay))  # one n_N square on diagonal
        conn_stim = p.FromListConnector(connections_stim)
        stim.append(p.Population(n_stim, p.SpikeSourcePoisson(rate=10.0, start=init_skew*(s+1)), label="Stim"+str(s)))
        p.Projection(stim[s], cell[x][y], conn_stim, syn_stim, receptor_type="excitatory")
        s += 1

#
# initialize the network, run, and get results
#

for x, y in product(range(9), repeat=2):
    cell[x][y].initialize(v=RandomDistribution("uniform", low=-65.0, high=-55.0))
    cell[x][y].record("spikes")

p.run(run_time)

fp = open("sudoku_spikes", "wb")            # save parameters & initial state
params = [run_time, n_cell]
numpy.save(fp, params)
numpy.save(fp, init)
numpy.save(fp, corr)

f, axarr = pylab.subplots(9, 9)
for x, y in product(range(9), repeat=2):
    neuron_ids = []
    spike_times = []
    for spiketrain in cell[x][y].get_data().segments[0].spiketrains:
        for t in spiketrain:
            neuron_ids.append(spiketrain.annotations["source_index"])
            spike_times.append(t)

    numpy_spikes = numpy.vstack((neuron_ids, spike_times)).T
    #numpy_spikes = numpy_spikes[numpy.lexsort((spike_times, neuron_ids))]
    numpy.save(fp, numpy_spikes)
    axarr[8-y][x].plot([i[1] for i in numpy_spikes], [i[0] for i in numpy_spikes], "b,")
    axarr[8-y][x].axis([0, run_time, -1, n_cell + 1])
    axarr[8-y][x].axis('off')
pylab.savefig("sudoku.png")

p.end()                                     # shut down the SpiNNaker machine
