# Import modules
import numpy as np
import pytest
import pynn_spinnaker as sim

# Import classes
from pyNN.random import NumpyRNG, RandomDistribution
from pynn_spinnaker.spinnaker.utils import UnitStrideSlice

# Import functions
from scipy.stats import binned_statistic, ks_2samp


native_rng = sim.NativeRNG(NumpyRNG())

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _run_network(pop_size_1, pop_size_2, connector, synapse, required_params, dt=1.0):
    # Setup simulator
    sim.setup(timestep=dt, stop_after_loader=True)

    # Create two populations
    pre = sim.Population(pop_size_1, sim.IF_curr_exp())
    post = sim.Population(pop_size_2, sim.IF_curr_exp())

    # As we're not actually simulating the network, give a low
    # mean firing rate estimate so partitioning will be optimistic
    pre.spinnaker_config.mean_firing_rate = 0.1

    # Connect the populations together
    proj = sim.Projection(pre, post, connector,
                          synapse)

    # Check that projection will be generated on chip
    assert proj._can_generate_on_chip

    # Run for a token period (it's ignored as we're stopping after load)
    sim.run(1)

    # Read data from projection
    proj_data = proj.get(required_params, format="list")

    # Unzip and return
    return proj, zip(*proj_data)

@pytest.mark.parametrize("pop_size_1,pop_size_2,num_connections",
                         [(547,547,52147),(106,1439,3049),(294,583,0),(294,294,13506),(485,547,877),
                          (294,2068,0),(1439,2068,22711),(485,106,3181),(485,485,20407),(106,294,251),
                          (547,1439,13198),(2191,583,41025),(1439,106,1318),(583,485,18171),(583,2068,223203),
                          (583,106,1686),(583,583,50153),(294,106,0),(294,2191,0),(294,1439,108239),
                          (2191,2068,202507),(2068,2191,35029),(547,294,81),(2068,547,81009),(2191,2191,244773),
                          (2068,294,22547),(106,106,4284),(106,2068,0),(2068,1439,46796),(2191,1439,67252),
                          (106,485,24079),(106,583,0),(2191,547,99172),(547,106,128),(583,294,172),
                          (2068,2068,454932),(1439,485,14390),(1439,547,87964),(1439,1439,83697),(2068,485,106136),
                          (1439,2191,146211),(1439,294,28806),(485,2191,7144),(2068,583,174317),(547,485,1519),
                          (2191,294,2194),(547,2068,96695),(485,2068,32931),(547,2191,174096),(583,2191,7564),
                          (485,1439,41108),(583,547,927),(485,294,4005),(547,583,16889),(1439,583,3532),
                          (294,547,0),(294,485,0),(583,1439,5559),(2068,106,12356),(485,583,22197),
                          (2191,485,55078),(106,547,0),(106,2191,70),(2191,106,6048)])
def test_microcircuit_projections(pop_size_1, pop_size_2, num_connections):

    connector = sim.FixedTotalNumberConnector(num_connections,
                                              with_replacement=True,
                                              rng=native_rng)

    proj, proj_data = _run_network(pop_size_1, pop_size_2, connector,
                                   sim.StaticSynapse(weight=0.0, delay=0.1),
                                   [])

    # Estimate maximum and mean row length
    pre_slice = UnitStrideSlice(0, pop_size_1)
    post_slice = UnitStrideSlice(0, pop_size_2)
    estimated_max_row_synapses = connector._estimate_max_row_synapses(
        pre_slice, post_slice, pop_size_1, pop_size_2)
    estimated_mean_row_synapses = connector._estimate_mean_row_synapses(
        pre_slice, post_slice, pop_size_1, pop_size_2)

    # Build row-length histogram
    row_length_histogram = binned_statistic(proj_data[0], proj_data[1],
                                            statistic="count", bins=range(pop_size_1 + 1))[0]

    # Test that the number of connections is correct
    assert int(row_length_histogram.sum()) == num_connections

    # Computer max and mean
    actual_max_row_synapses = np.amax(row_length_histogram)
    actual_mean_row_synapses = np.average(row_length_histogram)

    # Check estimated maximum is greater or equal than actual maximum
    assert estimated_max_row_synapses >= actual_max_row_synapses
