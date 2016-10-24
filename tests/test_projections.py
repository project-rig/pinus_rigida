# Import modules
import numpy as np
import pytest
import pynn_spinnaker as sim

# Import classes
from pynn_spinnaker.spinnaker.synapse_cluster import WeightRange
from pynn_spinnaker.spinnaker.utils import UnitStrideSlice

# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("pre_size", [100])
@pytest.mark.parametrize("post_size, post_slice",
                         [(500, UnitStrideSlice(0, 100)),
                          (500, UnitStrideSlice(100, 200)),
                          (500, UnitStrideSlice(400, 500))])
@pytest.mark.parametrize("view_slice",
                         [slice(0, 100),
                          slice(0, 20),
                          slice(40, 80),
                          slice(80, 100)])
def test_pre_view_connections(pre_size, post_size, post_slice, view_slice):
    sim.setup(timestep=1.0)

    pre_pop = sim.Population(pre_size, sim.IF_curr_exp())
    post_pop = sim.Population(post_size, sim.IF_curr_exp())
    pre_view = pre_pop[view_slice]

    proj = sim.Projection(pre_view, post_pop, sim.AllToAllConnector(),
                          sim.StaticSynapse(weight=1.0))

    # Create list of lists to contain matrix rows
    sub_rows = [[] for _ in range(pre_pop.size)]

    # Create weight range
    weight_range = WeightRange(sim.StaticSynapse._signed_weight)

    # Local mask to select only the columns
    # corresponding to neurons in postsynaptic vertex
    proj.post._mask_local = np.zeros((post_size,), dtype=bool)
    proj.post._mask_local[post_slice.python_slice] = True

    # Build projection
    proj._build(matrix_rows=sub_rows,
                weight_range=weight_range,
                directly_connect=False,
                underlying_pre_indices=pre_view._underlying_indices,
                underlying_post_indices=post_pop._underlying_indices)

    # Loop through rows BEFORE view slice begins
    for row in sub_rows[:view_slice.start]:
        assert len(row) == 0
    # Loop through rows in slice
    for row in sub_rows[view_slice]:
        assert len(row) == len(post_slice)
    # Loop through rows AFTER view slice stops
    for row in sub_rows[view_slice.stop:]:
        assert len(row) == 0