# Import modules
import numpy as np

# Import classes
from parameter_space import ParameterSpace

# ------------------------------------------------------------------------------
# SpikeSourcePoisson
# ------------------------------------------------------------------------------
class SpikeSourcePoisson(ParameterSpace):
    SeedWords = 4

    def __init__(self, cell_type, parameters, initial_values,
                 sim_timestep_ms, pop_size):
        # Superclass
        super(SpikeSourcePoisson, self).__init__(
            None, cell_type.immutable_param_map,
            parameters, initial_values, pop_size,
            sim_timestep_ms=sim_timestep_ms)


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
        # Add size of seed to size of base class parameters
        return (SpikeSourcePoisson.SeedWords * 4) +\
            super(SpikeSourcePoisson, self).sizeof(vertex_slice)


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

        # Write seed
        seed = np.random.randint(
            0x7FFFFFFF, size=SpikeSourcePoisson.SeedWords).astype(np.uint32)
        fp.write(seed.tostring())

        # Write parameter space to file
        super(SpikeSourcePoisson, self).write_subregion_to_file(fp,
                                                                vertex_slice)
