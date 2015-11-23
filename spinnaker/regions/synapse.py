# Import modules
from .. import lazy_param_map
import struct

# Import classes
from region import Region

#------------------------------------------------------------------------------
# Synapse
#------------------------------------------------------------------------------
class Synapse(Region):
    def __init__(self, cell_type, parameters, initial_values, sim_timestep_ms):
        num_neurons = parameters.shape[0]

        # Use neurons mutable parameter map to
        # transform lazy array of mutable parameters
        self.mutable_params = lazy_param_map.apply(
            initial_values, cell_type.synapse_mutable_param_map,
            num_neurons, sim_timestep_ms)

        # Use neurons immutable parameter map to transform
        # lazy array of immutable parameters
        self.immutable_params = lazy_param_map.apply(
            parameters, cell_type.synapse_immutable_param_map,
            num_neurons, sim_timestep_ms)
    
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
        
        # Add storage size of parameter slice to header and return
        return self.immutable_params[vertex_slice.python_slice].nbytes +\
            self.mutable_params[vertex_slice.python_slice].nbytes

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
        # Write parameter slices as string
        fp.write(self.mutable_params[vertex_slice.python_slice].tostring())
        fp.write(self.immutable_params[vertex_slice.python_slice].tostring())