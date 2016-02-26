# Import modules
import numpy as np
import struct
from .. import lazy_param_map

# Import classes
from region import Region


# ------------------------------------------------------------------------------
# ParameterSpace
# ------------------------------------------------------------------------------
class ParameterSpace(Region):
    def __init__(self, mutable_param_map, immutable_param_map,
                 parameters, initial_values, **kwargs):
        # Use mutable parameter map to
        # transform lazy array of mutable parameters
        self.mutable_params = lazy_param_map.apply(
            initial_values, mutable_param_map,
            parameters.shape[0], **kwargs)

        # Use neurons immutable parameter map to transform
        # lazy array of immutable parameters
        self.immutable_params = lazy_param_map.apply(
            parameters, immutable_param_map,
            parameters.shape[0], **kwargs)

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

        # Find unique immutable synapse parameter slice
        unique_immutable = np.unique(
            self.immutable_params[vertex_slice.python_slice])

        # Add size of unique parameter count and mutable parameters slice
        return 4 + (len(vertex_slice) * 2) + unique_immutable.nbytes +\
            self.mutable_params[vertex_slice.python_slice].nbytes

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
        # Find unique immutable synapse parameter slice
        unique_immutable = np.unique(
            self.immutable_params[vertex_slice.python_slice],
            return_inverse=True)

        # Write mutable parameter slice as string
        fp.write(self.mutable_params[vertex_slice.python_slice].tostring())

        # Write number of unique immutable parameters
        fp.write(struct.pack("I", len(unique_immutable[0])))

        # Write indices into unique_immutable array
        fp.write(unique_immutable[1].astype(np.uint16).tostring())

        # Write unique immutable parameters
        fp.write(unique_immutable[0].tostring())
