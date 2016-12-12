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
def _run_network(pop_size, connector, synapse, required_params, dt=1.0):
    # Setup simulator
    sim.setup(timestep=dt, stop_after_loader=True)

    # Create two populations
    pre = sim.Population(pop_size, sim.IF_curr_exp())
    post = sim.Population(pop_size, sim.IF_curr_exp())

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

# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("pop_size", [200, 2000])
@pytest.mark.parametrize("synapse",
                         [sim.StaticSynapse(weight=0.0, delay=4.0),
                          sim.StaticSynapse(weight=0.0, delay=10.0),
                          sim.STDPMechanism(
                              timing_dependence=sim.SpikePairRule(A_plus=0.0, A_minus=0.0),
                              weight_dependence=sim.AdditiveWeightDependence(w_min=0.0, w_max=1.0),
                              weight=0.0, delay=4.0),
                          sim.STDPMechanism(
                              timing_dependence=sim.SpikePairRule(A_plus=0.0, A_minus=0.0),
                              weight_dependence=sim.AdditiveWeightDependence(w_min=0.0, w_max=1.0),
                              weight=0.0, delay=10.0)])
def test_static_delay(pop_size, synapse):
    # Run network
    proj, proj_data = _run_network(pop_size, sim.AllToAllConnector(),
                                   synapse, ["delay"])

    # Check they all match
    delay = synapse.native_parameters["delay"].base_value
    assert all(d == delay for d in proj_data[2])

@pytest.mark.parametrize("pop_size", [200, 2000])
@pytest.mark.parametrize("connector",
                         [sim.AllToAllConnector(),
                          sim.FixedProbabilityConnector(0.1, rng=native_rng)])
def test_connector_metrics(pop_size, connector):
    # Run network
    proj, proj_data = _run_network(pop_size, connector,
                                   sim.StaticSynapse(weight=0.0, delay=1.0),
                                   [])

    # Estimate maximum and mean row length
    pop_slice = UnitStrideSlice(0, pop_size)

    # Distribution over synapses per row per post slice
    row_synapses_distribution = connector._row_synapses_distribution(
        pop_slice, pop_slice, pop_size, pop_size)

    estimated_max_row_synapses = row_synapses_distribution.ppf(0.9999 ** (1.0 / pop_size))
    estimated_mean_row_synapses = row_synapses_distribution.mean()

    # Build row-length histogram
    row_length_histogram = binned_statistic(proj_data[0], proj_data[1],
                                            statistic="count", bins=range(pop_size + 1))[0]

    # Computer max and mean
    actual_max_row_synapses = np.amax(row_length_histogram)
    actual_mean_row_synapses = np.average(row_length_histogram)

    # Check estimated maximum is greater or equal than actual maximum
    assert estimated_max_row_synapses >= actual_max_row_synapses

    # Check estimated maximum isn't TOO big
    assert estimated_max_row_synapses <= actual_max_row_synapses * 1.25

    # Check estimated mean is approximately correct
    assert estimated_mean_row_synapses <= (1.25 * actual_mean_row_synapses)
    assert estimated_mean_row_synapses >= (0.75 * actual_mean_row_synapses)

# Due to issue #65 large population sizes, without replacement stick in an infinite loop
#@pytest.mark.parametrize("pop_size", [200, 2000])
#@pytest.mark.parametrize("connection_proportion", [0.05, 0.2])
#@pytest.mark.parametrize("with_replacement", [True, False])
@pytest.mark.parametrize("pop_size, connection_proportion, with_replacement",
                         [(200, 0.05, True),
                          (200, 0.05, False),
                          (200, 0.2, True),
                          (200, 0.2, False),
                          (2000, 0.05, True),
                          (2000, 0.2, True)])
def test_fixed_number_connector(pop_size, connection_proportion, with_replacement):

    num_connections = int(connection_proportion * pop_size**2)
    connector = sim.FixedTotalNumberConnector(num_connections,
                                              with_replacement=with_replacement,
                                              rng=native_rng)

    proj, proj_data = _run_network(pop_size, connector,
                                   sim.StaticSynapse(weight=0.0, delay=1.0),
                                   [])

    # Estimate maximum and mean row length
    pop_slice = UnitStrideSlice(0, pop_size)

    # Distribution over synapses per row per post slice
    row_synapses_distribution = connector._row_synapses_distribution(
        pop_slice, pop_slice, pop_size, pop_size)

    estimated_max_row_synapses = row_synapses_distribution.ppf(0.9999 ** (1.0 / pop_size))
    estimated_mean_row_synapses = row_synapses_distribution.mean()

    # Build row-length histogram
    row_length_histogram = binned_statistic(proj_data[0], proj_data[1],
                                            statistic="count", bins=range(pop_size + 1))[0]

    assert int(row_length_histogram.sum()) == num_connections

    # Computer max and mean
    actual_max_row_synapses = np.amax(row_length_histogram)
    actual_mean_row_synapses = np.average(row_length_histogram)

    # Check estimated maximum is greater or equal than actual maximum
    assert estimated_max_row_synapses >= actual_max_row_synapses

    # Check estimated maximum isn't TOO big
    assert estimated_max_row_synapses <= actual_max_row_synapses * 3.0

    # Check estimated mean is approximately correct
    assert estimated_mean_row_synapses <= (1.25 * actual_mean_row_synapses)
    assert estimated_mean_row_synapses >= (0.75 * actual_mean_row_synapses)


@pytest.mark.parametrize("delay_dist_name_params", [("normal_clipped", [1.5, 0.75, 0.1, 1000.0])])
def test_connector_delay_dist(delay_dist_name_params):
    # Build PyNN distribution object
    delay_dist = RandomDistribution(delay_dist_name_params[0],
                                    delay_dist_name_params[1],
                                    rng=native_rng)
    # Run network
    proj, proj_data = _run_network(1000, sim.AllToAllConnector(),
                                   sim.StaticSynapse(weight=0.0, delay=delay_dist),
                                   ["delay"], 0.1)

    # Generate some samples from original distribution
    samples = delay_dist.next(len(proj_data))
    samples = np.around(samples, decimals=1)

    # Run Kolmogorov-Smirnov test on data
    test = ks_2samp(proj_data[2], samples)
    assert test[1] > 0.05

@pytest.mark.parametrize("weight_dist_name_params",
                         [("normal_clipped", [0.277647978563, 0.0277647978563, 0.0, 1000.0], False),
                          ("normal_clipped", [-1.11059191425, 0.111059191425, -1000.0, 0.0], True),
                          ("uniform", [0.0, 0.01], False)])
def test_connector_weight_dist(weight_dist_name_params):
    # Build PyNN distribution object
    weight_dist = RandomDistribution(weight_dist_name_params[0],
                                     weight_dist_name_params[1],
                                     rng=native_rng)

    # Run network
    proj, proj_data = _run_network(1000, sim.AllToAllConnector(),
                                   sim.StaticSynapse(weight=weight_dist, delay=1.0),
                                   ["weight"], 1.0)

    # **HACK** because of issue #60 
    if weight_dist_name_params[2]:
        proj_data[2] = np.multiply(proj_data[2], -1)

    # Generate some samples from original distribution
    samples = weight_dist.next(len(proj_data))

    # Run Kolmogorov-Smirnov test on data
    test = ks_2samp(proj_data[2], samples)
    assert test[1] > 0.05
