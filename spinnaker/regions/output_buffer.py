# Import modules
import numpy as np
import struct

# Import classes
from region import Region
from six import itervalues

# ------------------------------------------------------------------------------
# OutputBuffer
# ------------------------------------------------------------------------------
class OutputBuffer(Region):
    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self, out_buffers):
        """Get the size requirements of the region in bytes.

        Parameters
        ----------
        vertex_slice : :py:func:`slice`
            A slice object which indicates which rows, columns or other
            elements of the region should be included.
        formatter_args : optional
            Arguments which will be passed to the (optional) formatter along
            with each value that is being written.

        Returns
        -------
        int
            The number of bytes required to store the data in the given slice
            of the region.
        """
        # Two pointers
        return 2 * 4

    def write_subregion_to_file(self, fp, out_buffers):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        vertex_slice : :py:func:`slice`
            A slice object which indicnamedtupleates which rows, columns or other
            elements of the region should be included.
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        formatter_args : optional
            Arguments which will be passed to the (optional) formatter along
            with each value that is being written.
        """
        assert len(out_buffers) == 2
        
        # Write output buffer pointers to file
        fp.write(struct.pack("II", *out_buffers))