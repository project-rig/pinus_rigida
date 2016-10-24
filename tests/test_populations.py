# Import modules
import numpy as np
import pytest
import pynn_spinnaker as sim

# Import classes
from pyNN.parameters import LazyArray
from pyNN.random import NumpyRNG, RandomDistribution

# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def test_underlying_populations():
    # Setup simulator
    sim.setup(timestep=1.0, min_delay=1.0, max_delay=8.0)

    # Create some populations
    pop_a = sim.Population(10, sim.IF_curr_exp())
    pop_b = sim.Population(10, sim.IF_curr_exp())
    pop_c = sim.Population(10, sim.IF_curr_exp())

    # Test populations
    assert pop_a._underlying_populations == set((pop_a,))

    # Test view
    view_a = sim.PopulationView(pop_a, slice(0, 5))
    assert view_a._underlying_populations == set((pop_a,))

    # Test assembly
    assembly_a_b = sim.Assembly(pop_a, pop_b)
    assert assembly_a_b._underlying_populations == set((pop_a, pop_b))

    # Test view of views
    view_view_a = sim.PopulationView(view_a, slice(0, 2))
    assert view_view_a._underlying_populations == set((pop_a,))

    # **NOTE** not supported by PyNN
    # Test assembly of assemblies
    #assembly_c_assembly_a_b = sim.Assembly(assembly_a_b, pop_c)
    #assert assembly_c_assembly_a_b._underlying_populations == set((pop_a, pop_b, pop_c))

    # Test assembly of views
    view_b = sim.PopulationView(pop_b, slice(0, 5))
    assembly_view_a_view_b = sim.Assembly(view_a, view_b)
    assert assembly_view_a_view_b._underlying_populations == set((pop_a, pop_b))

    # **NOTE** seems to be a PyNN bug in creating these
    # Test view of assemblies
    #view_assembly_a_b = sim.PopulationView(assembly_a_b, slice(0, 10))
    #assert view_assembly_a_b._underlying_populations == set((pop_a, pop_b))


def test_mean_firing_rate():
    # Setup simulator
    sim.setup(timestep=1.0, min_delay=1.0, max_delay=8.0)

    # Create some populations
    pop_a = sim.Population(10, sim.IF_curr_exp())
    pop_a.spinnaker_config.mean_firing_rate = 5.0

    pop_b = sim.Population(20, sim.IF_curr_exp())
    pop_b.spinnaker_config.mean_firing_rate = 20.0

    # Test populations
    assert pop_a._mean_firing_rate == 5.0
    assert pop_b._mean_firing_rate == 20.0

    # Test view
    view_a = sim.PopulationView(pop_a, slice(0, 5))
    view_a._mean_firing_rate == 5.0

    # Test assembly
    assembly_a_b = sim.Assembly(pop_a, pop_b)
    assert assembly_a_b._mean_firing_rate == ((5.0 * 10.0) + (20.0 * 20.0)) / 30.0

    # Test view of views
    view_view_a = sim.PopulationView(view_a, slice(0, 2))
    assert view_view_a._mean_firing_rate == 5.0

    # **NOTE** not supported by PyNN
    # Test assembly of assemblies
    #assembly_c_assembly_a_b = sim.Assembly(assembly_a_b, pop_c)

    # Test assembly of views
    view_b = sim.PopulationView(pop_b, slice(0, 5))
    assembly_view_a_view_b = sim.Assembly(view_a, view_b)
    assert assembly_view_a_view_b._mean_firing_rate == ((5.0 * 5.0) + (20.0 * 5.0)) / 10.0

    # **NOTE** seems to be a PyNN bug in creating these
    # Test view of assemblies
    #view_assembly_a_b = sim.PopulationView(assembly_a_b, slice(0, 10))

def test_underlying_indices():
    # Setup simulator
    sim.setup(timestep=1.0, min_delay=1.0, max_delay=8.0)

    # Create some populations
    pop_a = sim.Population(10, sim.IF_curr_exp())
    pop_b = sim.Population(10, sim.IF_curr_exp())
    pop_c = sim.Population(10, sim.IF_curr_exp())

    # Test populations
    assert np.array_equal(pop_a._underlying_indices, np.arange(10))
    assert np.array_equal(pop_b._underlying_indices, np.arange(10))

    # Test view
    view_a = sim.PopulationView(pop_a, slice(0, 5))
    assert np.array_equal(view_a._underlying_indices, np.arange(5))

    # Test assembly
    assembly_a_b = sim.Assembly(pop_a, pop_b)
    assembly_a_b_indices = np.concatenate((np.arange(10), np.arange(10)))
    assert np.array_equal(assembly_a_b._underlying_indices, assembly_a_b_indices)

    # Test view of views
    view_view_a = sim.PopulationView(view_a, slice(3, 5))
    assert np.array_equal(view_view_a._underlying_indices, np.arange(3, 5))

    # **NOTE** not supported by PyNN
    # Test assembly of assemblies
    #assembly_c_assembly_a_b = sim.Assembly(assembly_a_b, pop_c)
    #assert assembly_c_assembly_a_b._underlying_populations == set((pop_a, pop_b, pop_c))

    # Test assembly of views
    view_b = sim.PopulationView(pop_b, slice(2, 7))
    assembly_view_a_view_b = sim.Assembly(view_a, view_b)
    assert np.array_equal(assembly_view_a_view_b._underlying_indices,
                          np.concatenate((np.arange(5), np.arange(2, 7))))

    # **NOTE** seems to be a PyNN bug in creating these
    # Test view of assemblies
    #view_assembly_a_b = sim.PopulationView(assembly_a_b, slice(0, 10))
    #assert view_assembly_a_b._underlying_populations == set((pop_a, pop_b))
