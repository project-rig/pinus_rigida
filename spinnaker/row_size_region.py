# Import modules
import numpy as np
import struct

# Import classes
from collections import OrderedDict
from rig.regions.region import Region

# **YUCK** duplication
ROW_HEADER_BYTES = 3 * 4

#------------------------------------------------------------------------------
# RowSizeRegion
#------------------------------------------------------------------------------
class RowSizeRegion(Region):
    def __init__(self, max_entries = 8, max_row_size = 1044):
        self.max_entries = max_entries
        self.max_row_size = max_row_size
       
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
        
        # Region is always a fixed size table
        return 4 * self.max_entries

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
        
        # Extract row sizes from formatter
        row_sizes = formatter_args["row_sizes"]
    
    #--------------------------------------------------------------------------
    # Public methods
    #--------------------------------------------------------------------------
    def calc_row_sizes(self, matrices, vertex_slice):
        """From a dictionary of synaptic matrices, builds an optimal list of
        row sizes for a given vertex slice

        Parameters
        ----------
        matrices : dict
            A dictionary of pre-synaptic populations to numpy synaptic matrices
        vertex_slice : :py:func:`slice`
            A slice object which indicates which rows, columns or other
            elements of the region should be included.
            
        Returns
        -------
        list uint32
            List of row sizes in bytes
        """

        # If there are no incoming connections, return an empty row_size table
        if len(matrices) == 0:
            return []
        else:
            # Loop through matrices
            all_max_row_sizes = []
            for m in matrices.itervalues():
                # Get slice of matrices for vertex
                sub_matrix = m[:,vertex_slice]
                
                # Get max row length of this matrix
                max_row_length = max(sub_matrix["mask"].sum(1))
                
                # Convert row lengths to bytes
                # **YUCK** duplication
                all_max_row_sizes.append(ROW_HEADER_BYTES + (4 * max_row_length))
            
            # Sort row sizes
            all_max_row_sizes.sort()

            # Check row sizes fall within maximum length
            if all_max_row_sizes[-1] > self.max_row_size:
                raise ValueError("Synaptic rows must fit within %u bytes" % self.max_row_size)
            
            # Divide space into number of available entries
            # **THINK** could we could chop off all but 1 max-length entries?
            step = float(len(all_max_row_sizes)) / float(self.max_entries)
            
            # As we need to include the last row size and 
            first_index = len(all_max_row_sizes) - 1 - int(round(7.0 * step))
            
            # Build row sizes from this
            row_sizes = [all_max_row_sizes[first_index + int(round(float(i) * step))] for i in range(self.max_entries)]
            
            # Remove duplicates and return
            return list(OrderedDict.fromkeys(row_sizes))