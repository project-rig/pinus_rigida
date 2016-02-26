# Import modules
import struct

# Import classes
from region import Region


# ------------------------------------------------------------------------------
# KeyLookupBinarySearch
# ------------------------------------------------------------------------------
class KeyLookupBinarySearch(Region):
    # How many of the low bits are used to represent row length
    NumSynapseBits = 10

    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self, sub_matrices, matrix_placements):
        """Get the size requirements of the region in bytes.

        Parameters
        ----------
        sub_matrices : list of :py:class:`._SubMatrix`
            Partitioned and expanded synaptic matrix rows
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
        return 4 + (len(sub_matrices) * 12)

    def write_subregion_to_file(self, fp, sub_matrices, matrix_placements):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        sub_matrices : list of :py:class:`._SubMatrix`
            Partitioned and expanded synaptic matrix rows
        matrix_placements : list of integers
            Offsets in words at which sub_matrices will be
            written into synaptic matrix region
        """
        # Write header
        data = b''
        data += struct.pack("I", len(sub_matrices))

        # Write each lookup entry
        # **NOTE** default sort is fine as first element of sub-matrix
        # tuple is key which is what we want to sort by
        for m, p in sorted(zip(sub_matrices, matrix_placements)):
            data += struct.pack(
                "III", m.key, m.mask,
                (m.max_cols - 1) | (p << KeyLookupBinarySearch.NumSynapseBits)
            )

        # Write data to filelike
        fp.write(data)

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
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
