# Import modules
import math
import numpy as np
import struct

# Import classes
from collections import namedtuple
from region import Region
from rig.type_casts import NumpyFloatToFixConverter

# Import functions
from bisect import bisect_left
from six import iteritems

SubMatrix = namedtuple("SubMatrix", ["key", "mask", "size_words",
                                     "max_cols", "matrix"])

#------------------------------------------------------------------------------
# SynapticMatrixRegion
#------------------------------------------------------------------------------
class SynapticMatrixRegion(Region):
    # Number of bits for various synapse components
    IndexBits = 10
    DelayBits = 3
  
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
        # Get the offset of last matrix, add its size and convert to bytes
        # **NOTE** assumes placement is monotonic
        sub_matrices = formatter_args["sub_matrices"]
        matrix_placements = formatter_args["matrix_placements"]
        if len(matrix_placements) == 0:
            return 0
        else:
            return 4 * (matrix_placements[-1] + sub_matrices[-1].size_words)
    
    def write_subregion_to_file(self, fp, vertex_slice, **formatter_args):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        vertex_slice : :py:func:`slice`
            A slice object which indicates which rows, columns or other
            elements of the region should be included.
        formatter_args : optional
            Arguments which will be passed to the (optional) formatter along
            with each value that is being written.
        """
        # Define record array type for rows
        row_dtype = [("w", np.float32),("d", np.float32),("i", np.uint32)]
        
        # Extract formatter arguments
        sub_matrices = formatter_args["sub_matrices"]
        matrix_placements = formatter_args["matrix_placements"]
        weight_fixed_point = formatter_args["weight_fixed_point"]
        
        # Create a numpy fixed point convert to convert
        # Floating point weights to this format
        # **NOTE** weights are only 16-bit, but final words need to be 32-bit
        float_to_weight = NumpyFloatToFixConverter(False, 32, 
                                                   weight_fixed_point)
        
        # Loop through sub matrices
        assert fp.tell() == 0
        for m, p in zip(sub_matrices, matrix_placements):
            print("Writing matrix placement:%u, max cols:%u" % (p, m.max_cols))
            
            # Seek to the absolute offset for this matrix
            fp.seek(p, 0)
            
            # Loop through matrix rows
            for r in m.matrix:
                # Convert row to numpy record array
                r_np = np.asarray(r, dtype=row_dtype)
                
                # Quantise delays
                # **TODO** take timestep into account
                d_quantised = np.empty(len(r_np), dtype=np.uint32)
                np.round(r_np["d"], out=d_quantised)
                
                # Convert weight to fixed point
                w_fixed = float_to_weight(r_np["w"])
                
                # Combine together into synaptic words
                words = np.empty(len(r_np) + 1, dtype=np.uint32)
                words[0] = len(r_np)
                words[1:] = (r_np["i"] 
                    | (d_quantised << SynapticMatrixRegion.IndexBits)
                    | (w_fixed << (SynapticMatrixRegion.IndexBits + SynapticMatrixRegion.DelayBits)))
                # Write words
                fp.write(words.tostring())
                print words
                # Seek forward by padding
                pad_words = m.max_cols - len(r_np)
                fp.seek(pad_words * 4, 1)

    #--------------------------------------------------------------------------
    # Public methods
    #--------------------------------------------------------------------------
    def partition_matrices(self, matrices, vertex_slice, incoming_connections):
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
                    for i, row in enumerate(rows):
                        # Extract indices
                        row_idxs = [s.index for s in row]

                        # Use bisect to find start and stop index of sub-row
                        # **NOTE** rows are already sorted by index
                        row_start = bisect_left(row_idxs, vertex_slice.start)
                        row_end = bisect_left(row_idxs, vertex_slice.stop)

                        # Use these to build sub-row indexed from slice start
                        sub_rows[i] = [(w, d, j - vertex_slice.start)
                                    for (w, d, j) in row[row_start:row_end]]

                    # Determine maximum number of columns in sub-matrix
                    max_cols = max([len(row) for row in rows])

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
                                    size_words,
                                    max_cols,
                                    sub_rows))

        return sub_matrices;
