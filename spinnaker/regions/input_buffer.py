# Import modules
import numpy as np
import struct

# Import classes
from region import Region
from six import itervalues

#------------------------------------------------------------------------------
# InputBuffer
#------------------------------------------------------------------------------
class InputBuffer(Region):
    #--------------------------------------------------------------------------
    # Region methods
    #--------------------------------------------------------------------------
    def sizeof(self, in_buffers):
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
        # A count followed by two words for each buffer
        return (1 + (4 * len(in_buffers))) * 4

    def write_subregion_to_file(self, fp, in_buffers):
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
        # Write header
        data = b''
        data += struct.pack("I", len(in_buffers))

        # Write each buffer entry
        for p, r, w in in_buffers:
            data += struct.pack("IIIi", p[0], p[1], r, 15 - w)

        # Write data to filelike
        fp.write(data)