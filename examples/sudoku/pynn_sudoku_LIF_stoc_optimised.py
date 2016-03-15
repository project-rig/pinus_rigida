#############################################################
#
# A PyNN Sudoku model
# Steve Furber, November 2015
#
#############################################################

#import pinus_rigida as p
import pyNN.nest as p

from   collections import defaultdict
from   itertools import product
import logging
import pylab
import numpy
from   pyNN.random import RandomDistribution

'''
logger = logging.getLogger("pinus_rigida")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

setup_kwargs = {
    "spinnaker_hostname": "192.168.1.1",
    "spinnaker_width": 8,
    "spinnaker_height": 8}
'''
setup_kwargs = {}

run_time  = 30000       # ms
fact      = 2.5         # number of neurons per digit/10
init_skew = 200.0       # ms - skew between successive input applications

p.setup(timestep=1.0, **setup_kwargs)
n_cell = int(90*fact)   # total number of neurons in a cell
n_stim = 30             # number of neurons in each stimulation (initialising) source
n_N    = n_cell/9       # number of neurons per value in cell

#global distributions & parameters
weight_cell = RandomDistribution("uniform", low=-0.2/fact, high=-0.0/fact)  # -0.2, 0.0
weight_stim = RandomDistribution("uniform", low=0.5, high=1.0)              # 0.5, 1.0
dur_nois    = RandomDistribution("uniform", low=25000.0, high=30000.0)      # 25000, 30000
weight_nois = 1.0                                                           # 1.6
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

def get_pop_start_index(count, x, y):
    return count * (x + (y * 9))

print("Creating populations")
cells = p.Population(n_cell * 9 * 9, p.IF_curr_exp(**cell_params_lif), label="Cells")

cells.initialize(v=RandomDistribution("uniform", low=-65.0, high=-55.0))
cells.record("spikes")

#
# add a noise source to each cell
#

noise = p.Population(n_cell* 9 * 9, p.SpikeSourcePoisson(rate=20.0, start=0.0, duration=dur_nois), label="Noise")

print("Creating noise projections")
syn_noise = p.StaticSynapse(weight=weight_nois)
conn_nois = p.OneToOneConnector()
p.Projection(noise, cells, conn_nois, syn_noise, receptor_type="excitatory")  # connect noise neurons one-to-one to cell neurons

#
# set up the cell internal inhibitory connections
#
print("Creating cell projections")
connections_cell = []
for x, y in product(range(9), repeat=2):
    pop_start =  get_pop_start_index(n_cell, x, y)
    connections_cell.extend([(i + pop_start, j + pop_start, 0.0 if i//n_N == j//n_N else weight_cell.next(), delay) for i in range(n_cell) for j in range(n_cell)])

syn_static = p.StaticSynapse()
conn_cell = p.FromListConnector(connections_cell)
p.Projection(cells, cells, conn_cell, syn_static, receptor_type="inhibitory")  # full constant matrix of weight_cell apart from n_N squares on diagonal

#
# set up the inter-cell inhibitory connections
#
print("Creating inter-cell projections")
def interCell(x, y, r, c):
    "Inhibit same number: connections are n_N squares on diagonal of weight_cell() from cell[x][y] to cell[r][c]"
    pop_start =  get_pop_start_index(n_cell, x, y)
    connections = []
    for i in range(n_cell):
        for j in range(n_N*(i//n_N), n_N*(i//n_N+1)): connections.append((pop_start + i, pop_start + j, weight_cell.next(), delay))
    return connections

connections_intC = []
for x, y in product(range(9), repeat=2):
    for r in range(9):
        if r != x: connections_intC.extend(interCell(x, y, r, y))                   # by row...
    for c in range(9):
        if c != y: connections_intC.extend(interCell(x, y, x, c))                   # by column...
    for r in range(3*(x//3),3*(x//3+1)):
        for c in range(3*(y//3),3*(y//3+1)):
            if r != x and c != y: connections_intC.extend(interCell(x, y, r, c))    # & by square
conn_intC = p.FromListConnector(connections_intC)
p.Projection(cells, cells, conn_intC, syn_static, receptor_type="inhibitory")
#
# set up & connect the initial (stimulation) conditions
#

connections_stim = []
for x, y in product(range(9), repeat=2):
    pop_start =  get_pop_start_index(n_cell, x, y)
    stim_start = get_pop_start_index(n_stim, x, y)
    if init[8-y][x] != 0:
        for i, j in product(range(n_stim), range(n_N*(init[8-y][x]-1), n_N*init[8-y][x])):
            connections_stim.append((stim_start + i, pop_start + j, weight_stim.next(), delay))  # one n_N square on diagonal

start_stim = numpy.repeat(init_skew * numpy.arange(1, (9 * 9) + 1), n_stim)
stim = p.Population(n_stim * 9 * 9, p.SpikeSourcePoisson(rate=10.0, start=start_stim), label="Stim")
syn_stim  = p.StaticSynapse()
conn_stim = p.FromListConnector(connections_stim)
p.Projection(stim, cells, conn_stim, syn_stim, receptor_type="excitatory")

#
#Run, and get results
#

p.run(run_time)

fp = open("sudoku_spikes", "ab")            # save parameters & initial state
params = [run_time, n_cell]
numpy.save(fp, params)
numpy.save(fp, init)
numpy.save(fp, corr)

# Group spike trains by cell
neuron_id = defaultdict(list)
spike_time = defaultdict(list)
for spiketrain in cells.get_data().segments[0].spiketrains:
    index = spiketrain.annotations["source_index"] % n_cell
    cell = spiketrain.annotations["source_index"] // n_cell

    x = cell % 9
    y = cell // 9

    for t in spiketrain:
        neuron_id[(x, y)].append(index)
        spike_time[(x,y)].append(t)

f, axarr = pylab.subplots(9, 9)
for x, y in product(range(9), repeat=2):
    cell_neuron_ids = neuron_id[(x,y)]
    cell_spike_times = spike_time[(x,y)]

    spikes = numpy.vstack((cell_neuron_ids,cell_spike_times)).T

    numpy.save(fp, spikes)
    axarr[8-y][x].plot([i[1] for i in spikes], [i[0] for i in spikes], "b,")
    axarr[8-y][x].axis([0, run_time, -1, n_cell + 1])
    axarr[8-y][x].axis('off')
pylab.savefig("sudoku.png")

p.end()                                     # shut down the SpiNNaker machine
