# Import modules
import itertools
import logging
import numpy as np

# Import classes
from collections import namedtuple
from region import Region
from rig.type_casts import NumpyFloatToFixConverter

# Import functions
from bisect import bisect_left
from operator import itemgetter
from six import iteritems
from ..utils import get_row_offset_length

SubMatrix = namedtuple("SubMatrix", ["key", "mask", "size_words",
                                     "max_cols", "rows"])

row_dtype = [("weight", np.float32), ("delay", np.uint32),
             ("index", np.uint32)]

logger = logging.getLogger("pinus_rigida")



# ------------------------------------------------------------------------------
# SynapticMatrix
# ------------------------------------------------------------------------------
class SynapticMatrix(Region):
    # Number of bits for various synapse components
    IndexBits = 10
    DelayBits = 3

    # How many bits are used to represent (extension) row length
    LengthBits = 10

    def __init__(self, max_dtcm_delay_slots):
        self.max_dtcm_delay_slots = max_dtcm_delay_slots

    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self, sub_matrices, matrix_placements, weight_fixed_point):
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
        # Get the offset of last matrix, add its size and convert to bytes
        # **NOTE** assumes placement is monotonic
        if len(matrix_placements) == 0:
            return 0
        else:
            return 4 * (matrix_placements[-1] + sub_matrices[-1].size_words)

    def write_subregion_to_file(self, fp, sub_matrices, matrix_placements,
                                weight_fixed_point):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        sub_matrices : list of :py:class:`._SubMatrix`
            Partitioned and expanded synaptic matrix rows
        matrix_placements : list of integers
            Offsets in words at which sub_matrices will be
            written into synaptic matrix region
        """
        # Create a numpy fixed point convert to convert
        # Floating point weights to this format
        # **NOTE** weights are only 16-bit, but final words need to be 32-bit
        float_to_weight = NumpyFloatToFixConverter(False, 32,
                                                   weight_fixed_point)

        # Loop through sub matrices
        assert fp.tell() == 0
        for matrix, placement in zip(sub_matrices, matrix_placements):
            # Seek to the absolute offset for this matrix
            # **NOTE** placement is in WORDS
            fp.seek(placement * 4, 0)

            # Build matrix large enough for entire ragged matri
            num_matrix_words = len(matrix.rows) * (3 + matrix.max_cols)
            matrix_words = np.empty((len(matrix.rows), 3 + matrix.max_cols),
                                    dtype=np.uint32)

            # Calculate the number of extension words required and build
            # Second numpy array to contain concatenated extension rows
            num_ext_words = matrix.size_words - num_matrix_words
            ext_words = np.empty(num_ext_words, dtype=np.uint32)

            logger.debug("\t\t\tWriting matrix placement:%u, max cols:%u, "
                         "matrix words:%u, num extension words:%u",
                         placement, matrix.max_cols, num_matrix_words,
                         matrix.size_words - num_matrix_words)

            # Loop through matrix rows
            next_row_offset = 0
            for i, row in enumerate(matrix.rows):
                # Write base row to matrix
                next_row = None if len(row) == 1 else row[1]
                self._write_spinnaker_row(row[0], next_row,
                                          placement + next_row_offset + num_matrix_words,
                                          float_to_weight, matrix_words[i])

                # Loop through extension rows
                for i, ext_row in enumerate(row[1:], start=1):
                    row_length = 3 + len(ext_row[1])
                    next_row = None if len(row) == (i + 1) else row[i + 1]
                    self._write_spinnaker_row(
                        ext_row, next_row,
                        placement + next_row_offset + row_length + num_matrix_words,
                        float_to_weight, ext_words[next_row_offset:])

                    next_row_offset += row_length

            # Write matrix followed by extension words
            fp.write(matrix_words.tostring())
            fp.write(ext_words.tostring())

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def partition_matrices(self, matrices, vertex_slice, incoming_connections):
        # Create lambda function to group delays into groups
        # that can be handled by the DTCM delay buffer
        delay_grouper = lambda d: (d[1] - 1) // self.max_dtcm_delay_slots

        # Loop through all incoming connections
        sub_matrices = []
        for pre_pop, pre_neuron_vertices in iteritems(incoming_connections):
            # Extract corresponding connection matrix
            matrix = matrices[pre_pop]

            # Loop through all the vertices that
            # make up the pre-synaptic population
            for pre_neuron_vertex in pre_neuron_vertices:
                # Slice the rows out of the matrix (fast)
                rows = matrix[pre_neuron_vertex.neuron_slice.python_slice]

                # If there are any rows
                if len(rows) > 0:
                    # Create a numpy array to hold the rows of the sub-matrix
                    # Connecting this pre-neuron vertex to this vertexs-lice
                    sub_rows = np.empty(len(rows), dtype=object)
                    max_cols = 0
                    num_extension_words = 0
                    any_connections = False
                    for i, row in enumerate(rows):
                        # Extract indices
                        row_idxs = [s.index for s in row]

                        # Use bisect to find start and stop index of sub-row
                        # **NOTE** rows are already sorted by index
                        row_start = bisect_left(row_idxs, vertex_slice.start)
                        row_end = bisect_left(row_idxs, vertex_slice.stop)

                        # Use these to build sub-row indexed from slice start
                        sub_row = [(w, d, j - vertex_slice.start)
                                   for (w, d, j) in row[row_start:row_end]]

                        # If sub-row has any elements
                        if len(sub_row) != 0:
                            # Set flag indicating this sub-matrix
                            # should actually be processed
                            any_connections = True

                            # Sort sub-row by delay
                            sub_row.sort(key=itemgetter(1))

                            # Group sub-row into delay groups
                            delay_row_iter = itertools.groupby(sub_row,
                                                               delay_grouper)
                            sub_rows[i] = [(e * self.max_dtcm_delay_slots,
                                            list(delay_row))
                                           for e, delay_row in delay_row_iter]

                            # If the first delay group of this sub-row
                            # isn't extended, add new empty sub-row
                            if sub_rows[i][0][0] != 0:
                                sub_rows[i].insert(0, (0, []))

                            # Count number of words in extension rows
                            for e in sub_rows[i][1:]:
                                num_extension_words += (3 + len(e[1]))

                            # Update maximum number of columns
                            max_cols = max(max_cols, len(sub_rows[i][0][1]))
                        # Otherwise, add empty row
                        else:
                            sub_rows[i] = [(0, [])]

                    # If there any connections within this sub-matrix
                    if any_connections:
                        # Calculate matrix size in words - size of square
                        # matrix added to number of extension words
                        # **NOTE** single header word required
                        size_words = num_extension_words +\
                            (len(sub_rows) * (3 + max_cols))

                        # Add sub matrix to list
                        sub_matrices.append(
                            SubMatrix(pre_neuron_vertex.key,
                                      pre_neuron_vertex.mask,
                                      size_words, max_cols, sub_rows))

        return sub_matrices

    def _write_spinnaker_row(self, row, next_row, next_row_offset,
                             float_to_weight, destination):
        # Write actual length of row (in synapses)
        destination[0] = len(row[1])

        # If there is no next row, write zeros to next two words
        if next_row is None:
            destination[1] = 0
            destination[2] = 0
        # Otherwise
        else:
            # Write relative delay of next_row from row
            destination[1] = (next_row[0] - row[0])

            # Write word containing the offset to the
            # next row and its length (in synapses)
            destination[2] = get_row_offset_length(next_row_offset,
                                                   len(next_row[1]),
                                                   self.LengthBits)

        # Convert row to numpy record array
        row = np.asarray(row[1], dtype=row_dtype)

        # Extract the DTCM component of delay
        dtcm_delay = 1 + ((row["delay"] - 1) % self.max_dtcm_delay_slots)

        # Convert weight to fixed point
        weight_fixed = float_to_weight(row["weight"])

        # How much should we shift weights to be above index and delay
        weight_shift = self.IndexBits + self.DelayBits

        # Write row
        destination[3:3 + len(row)] = (row["index"]
                                       | (dtcm_delay << self.IndexBits)
                                       | (weight_fixed << weight_shift))
