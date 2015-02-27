import struct
from rig.regions.region import Region

#------------------------------------------------------------------------------
# NeuronRegion
#------------------------------------------------------------------------------
class NeuronRegion(Region):
    def __init__(self, num_us_per_timestep, num_synapse_types, params):
        self.num_us_per_timestep = num_us_per_timestep
        self.num_synapse_types = num_synapse_types
        self.params = params
    
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
        
        # Calculate header size (one word for key, num_neurons, num_parameters,
        # num_microseconds_per_timestep and one for each synapse type)
        header_size = 4 * (4 + self.num_synapse_types)
        
        # Add storage size of parameter slice to header and return
        return header_size + self.params[vertex_slice].nbytes

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
        # Create parameter slice
        param_slice = self.params[vertex_slice]
        
        # Write header
        fp.write(struct.pack("IIII", 
                 formatter_args["key"],         # Routing key
                 len(param_slice),              # Number of neurons
                 len(self.params.dtype.names),  # Number of parameters(unused)
                 self.num_us_per_timestep))     # Time step length
        
        # Extract the per-synapse-type input shifts
        synapse_type_input_shifts = formatter_args["synapse_type_input_shifts"]
        
        # Write each synapse type's input shift
        fp.write(struct.pack("I" * self.num_synapse_types,
                             *synapse_type_input_shifts))
        
        # Write parameter slice as string
        fp.write(param_slice.tostring())
    
    #--------------------------------------------------------------------------
    # Properties
    #--------------------------------------------------------------------------
    @property
    def num_neurons(self):
        return len(self.params)
        