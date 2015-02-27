import numpy as np
import struct
from collections import namedtuple
from rig.regions.region import Region

# Number of bits for various synapse components
INDEX_BITS = 8
DELAY_BITS = 4
WEIGHT_BITS = 16

# Masks for various synapse components
INDEX_MASK = (1 << INDEX_BITS) - 1
DELAY_MASK = (1 << DELAY_BITS) - 1

INDEX_TYPE_BITS = INDEX_BITS + TYPE_BITS
    
# Define a named tuple type to contain arrays for mask, weight and delay
SynapticMatrix = namedtuple("SynapticMatrix", ["mask", "weight", "delay"])

#------------------------------------------------------------------------------
# SynapticMatrixRegion
#------------------------------------------------------------------------------
class SynapticMatrixRegion(Region):
    def __init__(self):
        # Dictionary of synaptic matrices associated with each incoming connection
        self.matrices = {}
       
    #--------------------------------------------------------------------------
    # Region methods
    #--------------------------------------------------------------------------
    def sizeof(self, vertex_slice):
        """Get the size requirements of the region in bytes.

        Parameters
        ----------
        vertex_slice : :py:func:`slice`
            A slice object which indicates which rows, columns or other
            elements of the region should be included.

        Returns
        -------
        int
            The number of bytes required to store the data in the given slice
            of the region.
        """
        
        pass

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
        weight_scale = formatter_args["weight_scale"]
        
        # **TODO** write base address
        
        # Loop through all incoming synaptic matrices
        for i, m in self.matrices.iteritems():
            # Get slice of matrices for vertex
            # **TODO** use record array
            sub_mask = m.mask[:,vertex_slice]
            sub_delay = m.delay[:,vertex_slice]
            sub_weight = m.weight[:,vertex_slice]
            
            # Get maximum row length of this synaptic matrix
            row_lengths = sub_mask.sum(1)
            max_row_length = max(row_lengths)
            
            print "Max row length:%u" % max_row_length
           
            # Build 1D arrays of post-synaptic neuron indices, weights and delays
            # **TODO** synapse types**
            post_indices = np.where(sub_mask == True)[1].astype(np.uint32)
            weights = np.rint(sub_weight[sub_mask] * weight_scale).astype(np.uint32)
            delays = sub_delay[sub_mask].astype(np.uint32)
            
            # Mask and shift these together to build 32-bit synaptic words
            synapse_words = ((post_indices & INDEX_MASK) | 
                ((delays & DELAY_MASK) << INDEX_TYPE_BITS) |
                weights << (32 - WEIGHT_BITS)).astype(np.uint32)
            
            # Determine how much weach row will need to be padded by
            row_pad_length = max_row_length - row_lengths
            
            # Cumulatively sum these to get the indices where rows end and
            # Duplicate these indices for the number of padding entries required
            row_end_indices = np.cumsum(row_lengths)
            where_to_pad = np.repeat(row_end_indices, row_pad_length)
            
            # Insert padding of zero at these locations
            padded_synapse_words = np.insert(synapse_words, where_to_pad, 0).reshape((sub_mask.shape[1], max_row_length))
            
            print padded_synapse_words
    
    #--------------------------------------------------------------------------
    # Public methods
    #--------------------------------------------------------------------------
    def convergent_connect(self, projection, pre_indices, post_index, 
                           **parameters):
        # **TODO** assemblies
        
        # If there's not already a synaptic matrix 
        # Associated with pre-synaptic population
        if projection.pre not in self.matrices:
            # Get shape of connection matrix
            shape = (len(projection.pre), len(projection.post))
            
            # Add synaptic matrix to dictionary
            # **NOTE** weights are kept floating point as 
            # Scale cannot be determined at this stage
            self.matrices[projection.pre] = SynapticMatrix(
                mask=np.zeros(shape, dtype=bool),
                weight=np.empty(shape, dtype=float),
                delay=np.empty(shape, dtype=np.uint8))
        
        # Quantise delay into timesteps
        quantised_delay = int(round(parameters["delay"]))
        
        # Set mask, weight and delay for column
        # **TODO** use record array
        matrix = self.matrices[projection.pre]
        matrix.mask[pre_indices, post_index] = True
        matrix.weight[pre_indices, post_index] = parameters["weight"]
        matrix.delay[pre_indices, post_index] = quantised_delay

        