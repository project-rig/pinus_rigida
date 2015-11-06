# Import modules
import numpy as np
import struct

# Import classes
from region import Region
from six import itervalues

#------------------------------------------------------------------------------
# KeyLookupBinarySearch
#------------------------------------------------------------------------------
class KeyLookupBinarySearch(Region):
    # How many of the low bits are used to represent row length
    NumSynapseBits = 10

    #--------------------------------------------------------------------------
    # Region methods
    #--------------------------------------------------------------------------
    def sizeof(self, vertex_slice, **formatter_args):
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
        # 1 word header followed by a 3 word struct for each sub-matrix
        return 4 + (len(formatter_args["sub_matrices"]) * 12)

    def write_subregion_to_file(self, fp, vertex_slice, **formatter_args):
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
        sub_matrices = formatter_args["sub_matrices"]
        matrix_placements = formatter_args["matrix_placements"]

        # Write header
        data = b''
        data += struct.pack("I", len(sub_matrices))

        # Write each lookup entry
        for m, p in zip(sub_matrices, matrix_placements):
            data += struct.pack(
                "III", m.key, m.mask,
                (m.max_cols - 1) | (p << KeyLookupBinarySearch.NumSynapseBits)
            )

        # Write data to filelike
        fp.write(data)

    #--------------------------------------------------------------------------
    # Public methods
    #--------------------------------------------------------------------------
    def place_matrices(self, sub_matrices):
        # Loop through sub-matrices
        matrix_placements = []
        current_offset_words = 0
        for sub_matrix in sub_matrices:
            # Add current offset
            matrix_placements.append(current_offset_words)

            # Add size to current offset
            current_offset_words += sub_matrix.size_words

        return matrix_placements
