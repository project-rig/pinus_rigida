# Import modules
import struct

# Import classes
from region import Region

#------------------------------------------------------------------------------
# SynapseRegion
#------------------------------------------------------------------------------
class SynapseRegion(Region):
    def __init__(self, num_us_per_timestep, num_synapse_types, params):
        self.num_us_per_timestep = num_us_per_timestep
        self.num_synapse_types = num_synapse_types
        self.params = params
    
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
        
        # Calculate header size (one word for key, num_neurons, num_parameters,
        # num_microseconds_per_timestep and one for each synapse type)
        header_size = 4 * (4 + self.num_synapse_types)
        
        # Add storage size of parameter slice to header and return
        return header_size + self.params[vertex_slice].nbytes

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
        # Create parameter slice
        param_slice = self.params[vertex_slice]