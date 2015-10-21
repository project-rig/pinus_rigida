import struct
from rig.regions.region import Region

#------------------------------------------------------------------------------
# NeuronRegion
#------------------------------------------------------------------------------
class NeuronRegion(Region):
    def __init__(self, mutable_params, immutable_params):
        self.mutable_params = mutable_params
        self.immutable_params = immutable_params
    
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
        # Write parameter slices as string
        fp.write(self.mutable_params[vertex_slice.python_slice].tostring())
        fp.write(self.immutable_params[vertex_slice.python_slice].tostring())
    
    #--------------------------------------------------------------------------
    # Properties
    #--------------------------------------------------------------------------
    @property
    def num_neurons(self):
        return len(self.immutable_params)
        