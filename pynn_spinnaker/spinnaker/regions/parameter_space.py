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
                 parameters, initial_values, pop_size, **kwargs):
        # Use mutable parameter map to
        # transform lazy array of mutable parameters
        if mutable_param_map is not None:
            self.mutable_params = lazy_param_map.apply(
                initial_values, mutable_param_map, pop_size, **kwargs)
        else:
            self.mutable_params = None

        # Use neurons immutable parameter map to transform
        # lazy array of immutable parameters
        if immutable_param_map is not None:
            self.immutable_params = lazy_param_map.apply(
                parameters, immutable_param_map, pop_size, **kwargs)
        else:
            self.immutable_params = None

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
        # If there are any mutable parameters
        size = 0
        if self.mutable_params is not None:
            size += self.mutable_params[vertex_slice.python_slice].nbytes

        # If there are any immutable parameters
        if self.immutable_params is not None:
            # Find unique immutable synapse parameter slice
            unique_immutable = np.unique(
                self.immutable_params[vertex_slice.python_slice])

            # Add size of unique parameter count and mutable parameters slice
            num_index_bytes = len(vertex_slice) * 2
            if len(vertex_slice) % 2 != 0:
                num_index_bytes += 2
            size += (4 + num_index_bytes + unique_immutable.nbytes)

        return size


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

        # Write mutable parameter slice as string
        if self.mutable_params is not None:
            fp.write(self.mutable_params[vertex_slice.python_slice].tostring())

        # If there are any immutable parameters
        if self.immutable_params is not None:
            # Find unique immutable synapse parameter slice
            unique_immutable = np.unique(
                self.immutable_params[vertex_slice.python_slice],
                return_inverse=True)

            # Write number of unique immutable parameters
            fp.write(struct.pack("I", len(unique_immutable[0])))

            # Write indices into unique_immutable array,
            # adding a padding half-word to word-align
            indices = unique_immutable[1].astype(np.uint16)
            fp.write(indices.tostring())
            if len(indices) % 2 != 0:
                fp.write(b"\x00\x00")

            # Write unique immutable parameters
            fp.write(unique_immutable[0].tostring())
