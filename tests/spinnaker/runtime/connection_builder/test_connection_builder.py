# Import modules
import numpy as np
import pytest
import pynn_spinnaker as sim


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _run_network(pop_size, weight, delay, required_params):
    # Setup simulator
    sim.setup(timestep=1.0, stop_after_loader=True)

    # Create two populations
    pre = sim.Population(pop_size, sim.IF_curr_exp())
    post = sim.Population(pop_size, sim.IF_curr_exp())

    # Connect the populations together
    proj = sim.Projection(pre, post, sim.AllToAllConnector(),
                          sim.StaticSynapse(weight=weight, delay=delay))
    assert proj._can_generate_on_chip

    # Run for a token period (it's ignored as we're stopping after load)
    sim.run(1)

    # Read data from projection
    proj_data = proj.get(required_params, format="list")

    # Check size
    assert len(proj_data) == (pop_size * pop_size)

    # Unzip and return
    return zip(*proj_data)

# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("pop_size", [200, 2000])
@pytest.mark.parametrize("delay", [4.0, 10.0])
def test_static_delay(pop_size, delay):
    # Run network
    proj_data = _run_network(pop_size, 0.0, delay, ["delay"])

    # Check they all match
    assert all(d == delay for d in proj_data[2])


