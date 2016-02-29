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

SubMatrix = namedtuple("SubMatrix", ["key", "mask", "size_words",
                                     "max_cols", "rows"])

logger = logging.getLogger("pinus_rigida")


# ------------------------------------------------------------------------------
# SynapticMatrix
# ------------------------------------------------------------------------------
class SynapticMatrix(Region):
    # Number of bits for various synapse components
    IndexBits = 10
    DelayBits = 3

    row_dtype = [("weight", np.float32), ("delay", np.uint32),
                 ("index", np.uint32)]

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

        # How much should we shift weights to be above index and delay
        weight_shift = self.IndexBits + self.DelayBits

        # Loop through sub matrices
        assert fp.tell() == 0
        for matrix, placement in zip(sub_matrices, matrix_placements):
            logger.debug("\t\t\tWriting matrix placement:%u, max cols:%u",
                         placement, matrix.max_cols)

            # Seek to the absolute offset for this matrix
            # **NOTE** placement is in WORDS
            fp.seek(placement * 4, 0)

            # Build matrix large enough for entire ragged matrix
            matrix_words = np.empty((len(matrix.rows), matrix.max_cols + 1),
                                    dtype=np.uint32)

            # Loop through matrix rows
            for i, row in enumerate(matrix.rows):
                # Convert row to numpy record array
                row = np.asarray(row, dtype=self.row_dtype)

                # Quantise delays
                # **TODO** take timestep into account
                delay_quantised = np.empty(len(row), dtype=np.uint32)
                np.round(row["delay"], out=delay_quantised)

                # Convert weight to fixed point
                weight_fixed = float_to_weight(row["weight"])

                # Combine together into synaptic words
                matrix_words[i, 0] = len(row)
                matrix_words[i, 1:1 + len(row)] = (
                    row["index"]
                    | (delay_quantised << self.IndexBits)
                    | (weight_fixed << weight_shift))

            # Write matrix
            fp.write(matrix_words.tostring())

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def partition_matrices(self, matrices, vertex_slice, incoming_connections):
        # Create lambda function to group delays into DTCM
        # **TODO** use synapse_type.max_dtcm_delay_slots
        delay_grouper = lambda d: d[1] // 8

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

                        # Sort sub-row by delay
                        print sub_row
                        sub_row.sort(key=itemgetter(1))
                        print sub_row
                        sub_rows[i] = [list(delay_group)
                                       for _, delay_group in itertools.groupby(sub_row, delay_grouper)]
                        print sub_rows[i]
                        assert False
                        # Update maximum columns
                        max_cols = max(max_cols, row_end - row_start)

                    # If there any columns in sub-matrix
                    if max_cols > 0:
                        # Calculate matrix size in words
                        # **TODO* extend to different formats
                        # **NOTE** single header word required
                        size_words = (len(sub_rows) * (1 + max_cols))

                        # Add sub matrix to list
                        sub_matrices.append(
                            SubMatrix(pre_neuron_vertex.key,
                                      pre_neuron_vertex.mask,
                                      size_words, max_cols, sub_rows))

        return sub_matrices
