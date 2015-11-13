# Import modules
import itertools
import math
import numpy as np
import struct

# Import classes
from region import Region

def bitfield_words(bits):
    return int(math.ceil(float(bits) / 32.0))

#------------------------------------------------------------------------------
# SpikeRecording
#------------------------------------------------------------------------------
class SpikeRecording(Region):
    def __init__(self, indices_to_record, simulation_ticks):
        self.indices_to_record = indices_to_record["spikes"]
        self.simulation_ticks = simulation_ticks

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
        #
        # Determine how many bytes are required for each neuron in slice
        indices_bytes = bitfield_words(vertex_slice.slice_length) * 4

        # Determine how many bytes are required for each index to record
        vertex_indices = self.indices_to_record[vertex_slice.python_slice]
        sample_bytes = bitfield_words(vertex_indices.count()) * 4

        # Header word specifiying how many words are in each sBitFieldample, indices
        # bit field and a sample bit field for each simulation tick
        return 4 + indices_bytes + (sample_bytes * self.simulation_ticks)

    def write_subregion_to_file(self, fp, vertex_slice, **formatter_args):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        vertex_slice : :py:func:`slice`
            A slice object which indicnamedtupleates which rows, columns or other
            elements of the region should be included.
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        formatter_args : optional
            Arguments which will be passed to the (optional) formatter along
            with each value that is being written.
        """
        # Slice out the vertex indices to record
        vertex_indices = self.indices_to_record[vertex_slice.python_slice]

        # Write number of bits required
        fp.write(struct.pack("I", bitfield_words(vertex_indices.count())))

        # Write bitfield to file
        # **NOTE** as there's no neurons after this,
        # the word-aligned bits don't matter
        fp.write(vertex_indices.tobytes())