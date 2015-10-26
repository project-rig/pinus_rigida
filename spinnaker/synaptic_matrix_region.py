# Import modules
import numpy as np
import struct

# Import classes
from collections import namedtuple
from region import Region

# Import functions
from bisect import bisect_left
from six import iteritems

SubMatrix = namedtuple("MatrixPlacement", ["key", "mask", "size_words",
                                           "max_cols", "matrix"])

#------------------------------------------------------------------------------
# SynapticMatrixRegion
#------------------------------------------------------------------------------
class SynapticMatrixRegion(Region):
    # Number of bits for various synapse components
    IndexBits = 10
    DelayBits = 3
    WeightBits = 16

    # Masks for various synapse components
    IndexMask = (1 << IndexBits) - 1
    DelayMask = (1 << DelayBits) - 1

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
        '''
        matrices = formatter_args["matrices"]
        matrix_placements = formatter_args["matrix_placements"]
        row_sizes = formatter_args["row_sizes"]
        
        # Loop through all incoming synaptic matrices
        total_size = 0
        for p, m in matrices.iteritems():
            # Get placement for this matrix
            placement = matrix_placements[p]
            
            # Get size of a row of matrix from table
            table_row_size = row_sizes[placement.row_size_index]
            
            # Multiply by number of rows to get matrix size and add this and 
            # Number of subsequent padding bytes to the total size
            total_size += (table_row_size * m.shape[1]) + placement.padding_bytes
        '''
        return 4
    
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
        '''
        matrices = formatter_args["matrices"]
        matrix_placements = formatter_args["matrix_placements"]
        row_sizes = formatter_args["row_sizes"]
        weight_scale = formatter_args["weight_scale"]
   
        # Loop through all incoming synaptic matrices
        for p, m in matrices.iteritems():
            # Get placement for this matrix
            placement = matrix_placements[p]
            
            # Get slice of matrices for vertex
            sub_matrix = m[:,vertex_slice]
       
            # Get maximum row length of this synaptic matrix
            sub_mask = sub_matrix["mask"]
            row_lengths = sub_mask.sum(1)
            
            # Get padded row length from row size table
            padded_row_length = row_sizes[placement.row_size_index]
            
            print "Padded row length:%u" % padded_row_length
           
            # Build 1D arrays of post-synaptic neuron indices, weights and delays
            # **TODO** synapse types**
            sparse_weight = sub_matrix["weight"][sub_mask]
            sparse_delay = sub_matrix["delay"][sub_mask]matrix_placements
            post_indices = np.where(sub_mask == True)[1].astype(np.uint32)
            weights = np.rint(sparse_weight * weight_scale).astype(np.uint32)
            delays = sparse_delay.astype(np.uint32)
            
            # Mask and shift these together to build 32-bit synaptic words
            synapse_words = ((post_indices & INDEX_MASK) | 
                ((delays & DELAY_MASK) << INDEX_TYPE_BITS) |
                weights << (32 - WEIGHT_BITS)).astype(np.uint32)
            
            # Determine how much weach row will need to be padded by
            row_pad_length = padded_row_length - row_lengths
            
            # Cumulatively sum these to get the indices where rows end and
            # Duplicate these indices for the number of padding entries required
            row_end_indices = np.cumsum(row_lengths)
            where_to_pad = np.repeat(row_end_indices, row_pad_length)
            
            # Insert padding of zero at these locations
            synapse_words = np.insert(synapse_words, where_to_pad, 0)

            # Write to file
            fp.write(synapse_words.tostring())
            
            # Seek forward by padding bytes 
            # **NOTE** 1 = SEEK_CUR
            fp.seek(placement.padding_bytes, 1)
        '''

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
