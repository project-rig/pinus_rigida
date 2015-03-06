import numpy as np
import struct
from rig.regions.region import Region

ROW_HEADER_BYTES = 3 * 4

# Number of bits for various synapse components
INDEX_BITS = 8
DELAY_BITS = 4
WEIGHT_BITS = 16
TYPE_BITS = 1

# Masks for various synapse components
INDEX_MASK = (1 << INDEX_BITS) - 1
DELAY_MASK = (1 << DELAY_BITS) - 1

INDEX_TYPE_BITS = INDEX_BITS + TYPE_BITS

#------------------------------------------------------------------------------
# SynapticMatrixRegion
#------------------------------------------------------------------------------
class SynapticMatrixRegion(Region):
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
        
        return total_size
    
    def write_subregion_to_file(self, vertex_slice, fp, **formatter_args):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        vertex_slice : :py:func:`slice`
            A slice object which indicates which rows, columns or other
            elements of the region should be included.
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        formatter_args : optional
            Arguments which will be passed to the (optional) formatter along
            with each value that is being written.
        """
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
            sparse_delay = sub_matrix["delay"][sub_mask]
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
    