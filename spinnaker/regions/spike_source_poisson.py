# Import modules
from .. import lazy_param_map
import lazyarray as la
import numpy as np
import struct

# Import classes
from region import Region

# Import functions
from copy import deepcopy


def get_param_slice(params, vertex_slice):
    # Find start and end of slice within parameters
    start = np.searchsorted(params["f0"], vertex_slice.start, side="left")
    stop = np.searchsorted(params["f0"], vertex_slice.stop, side="left")

    # Return slice
    return params[start:stop]


# ------------------------------------------------------------------------------
# SpikeSourcePoisson
# ------------------------------------------------------------------------------
class SpikeSourcePoisson(Region):
    # What is the maximum number of spikes per tick
    # when a 'slow' spike source is the best solution
    MaxSlowPerTick = 0.25
    SeedWords = 4

    def __init__(self, cell_type, parameters, initial_values, sim_timestep_ms):
        # Calculate mean spikes per-timestep each spike source will emit
        rates = deepcopy(parameters["rate"])
        spikes_per_timestep = (rates * sim_timestep_ms) / 1000.0

        # Based on this determine which spikes sources should be
        # simulated using the slow rather than fast model
        slow_mask = (spikes_per_timestep <= SpikeSourcePoisson.MaxSlowPerTick)
        fast_mask = la.logical_not(slow_mask)

        # Evaluate indices and turn to masks
        slow_indices = np.where(slow_mask.evaluate())[0]
        fast_indices = np.where(fast_mask.evaluate())[0]

        # Use slow spike source parameter map to
        # transform slice of lazy parameter array
        self.slow_params = lazy_param_map.apply_indices(
            parameters, cell_type.slow_immutable_param_map,
            slow_indices, sim_timestep_ms)

        # Use fast spike source parameter map to
        # transform slice of lazy parameter array
        self.fast_params = lazy_param_map.apply_indices(
            parameters, cell_type.fast_immutable_param_map,
            fast_indices, sim_timestep_ms)

    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self, vertex_slice):
        """Get the size requirements of the region in bytes.

        Parameters
        ----------
        vertex_slice : :py:func:`slice`
            A slice object which indicates which rows, columns or other
            elements of the region should be included.

        Returns
        -------
        int
            The number of bytes required to store the data in the given slice
            of the region.
        """

        # Find slices of slow and fast params
        slow_param_slice = get_param_slice(self.slow_params, vertex_slice)
        fast_param_slice = get_param_slice(self.fast_params, vertex_slice)

        # Size of region is the size of these slices,
        # two counters and seed words
        return slow_param_slice.nbytes + fast_param_slice.nbytes +\
            ((2 + SpikeSourcePoisson.SeedWords) * 4)

    def write_subregion_to_file(self, fp, vertex_slice):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        vertex_slice : :py:func:`slice`
            A slice object which indicates which rows, columns or other
            elements of the region should be included.
        """
        # Find slices of slow and fast params
        slow_param_slice = get_param_slice(self.slow_params, vertex_slice)
        fast_param_slice = get_param_slice(self.fast_params, vertex_slice)

        # **YUCK** make index field of parameter slices relative
        # to start of  slice - copy as trashing the copy owned
        # by the instance seems like a bad idea
        slow_param_slice = np.copy(slow_param_slice)
        fast_param_slice = np.copy(fast_param_slice)
        slow_param_slice["f0"] -= vertex_slice.start
        fast_param_slice["f0"] -= vertex_slice.start

        # Write seed
        seed = np.random.randint(
            0x7FFFFFFF, size=SpikeSourcePoisson.SeedWords).astype(np.uint32)
        fp.write(seed.tostring())

        # Write number of slow sources in slice followed by their parameters
        fp.write(struct.pack("I", len(slow_param_slice)))
        fp.write(slow_param_slice.tostring())

        # Write number of fast sources in slice followed by their parameters
        fp.write(struct.pack("I", len(fast_param_slice)))
        fp.write(fast_param_slice.tostring())
