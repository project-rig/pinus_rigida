# Import modules
import numpy as np
import struct
from .. import lazy_param_map

# Import classes
from region import Region


# ------------------------------------------------------------------------------
# HomogeneousParameterSpace
# ------------------------------------------------------------------------------
class HomogeneousParameterSpace(Region):
    def __init__(self, param_map, parameters, sim_timestep_ms):
        self.param_map = param_map
        self.parameters = parameters
        self.sim_timestep_ms = sim_timestep_ms

    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self, **kwargs):
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


        # Return size of parameter map when it's evaluated
        return lazy_param_map.size(self.param_map, 1)


    def write_subregion_to_file(self, fp, **kwargs):
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
        # Evaluate parameters
        parameters = lazy_param_map.apply(self.parameters,
                                          self.param_map, 1,
                                          sim_timestep_ms=self.sim_timestep_ms,
                                          **kwargs)
        # Write to file
        fp.write(parameters.tostring())