# Import modules
import struct

# Import classes
from region import Region

# Import functions
from ..utils import get_row_offset_length

# ------------------------------------------------------------------------------
# KeyLookupBinarySearch
# ------------------------------------------------------------------------------
class KeyLookupBinarySearch(Region):
    # How many bits are used to represent row length
    LengthBits = 10

    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self, sub_matrix_props, matrix_placements):
        """Get the size requirements of the region in bytes.

        Parameters
        ----------
        sub_matrix_props : list of :py:class:`._SubMatrix`
            Properties of the sub matrices to be written
            to synaptic matrix region
        matrix_placements : list of integers
            Offsets in words at which sub_matrices will be
            written into synaptic matrix region

        Returns
        -------
        int
            The number of bytes required to store the data in the given slice
            of the region.
        """
        # 1 word header followed by a 3 word struct for each sub-matrix
        return 4 + (len(sub_matrix_props) * 12)

    def write_subregion_to_file(self, fp, sub_matrix_props, matrix_placements):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        sub_matrix_props : list of :py:class:`._SubMatrix`
            Properties of the sub matrices to be written
            to synaptic matrix region
        matrix_placements : list of integers
            Offsets in words at which sub_matrices will be
            written into synaptic matrix region
        """
        # Write header
        data = b''
        data += struct.pack("I", len(sub_matrix_props))

        # Write each lookup entry
        # **NOTE** default sort is fine as first element of sub-matrix
        # tuple is key which is what we want to sort by
        for m, p in sorted(zip(sub_matrix_props, matrix_placements)):
            data += struct.pack(
                "III", m.key, m.mask,
                get_row_offset_length(p, m.max_cols, self.LengthBits)
            )

        # Write data to filelike
        fp.write(data)

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def place_matrices(self, sub_matrix_props):
        # Loop through sub-matrices
        matrix_placements = []
        current_offset_words = 0
        for s in sub_matrix_props:
            # Add current offset
            matrix_placements.append(current_offset_words)

            # Add size to current offset
            current_offset_words += s.size_words

        return matrix_placements
