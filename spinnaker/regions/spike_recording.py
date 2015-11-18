# Import modules
import itertools
import math
import numpy as np
import struct

# Import classes
from region import Region

def calc_bitfield_words(bits):
    return int(math.ceil(float(bits) / 32.0))

#------------------------------------------------------------------------------
# SpikeRecording
#------------------------------------------------------------------------------
class SpikeRecording(Region):
    def __init__(self, indices_to_record,
                 simulation_timestep_us, simulation_ticks):
        self.indices_to_record = indices_to_record["spikes"]
        self.simulation_timestep_ms = float(simulation_timestep_us) / 1000.0
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
        indices_bytes = self._calc_indices_bytes(vertex_slice)

        # Slice out the vertex indices to record
        vertex_indices = self.indices_to_record[vertex_slice.python_slice]
        sample_bytes = calc_bitfield_words(vertex_indices.count()) * 4

        # Header word specifiying how many words are in each sample, indices
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

        # Write number of words required to contain a suitable bitfield
        fp.write(struct.pack("I", calc_bitfield_words(vertex_indices.count())))

        # Write bitfield to file
        # **NOTE** as there's no neurons after this,
        # the word-aligned bits don't matter
        fp.write(vertex_indices.tobytes())

    #--------------------------------------------------------------------------
    # Public API
    #--------------------------------------------------------------------------
    def read_spike_times(self, vertex_slice, region_memory):
        # Get the indices within this vertes that were recorded
        vertex_indices = self.indices_to_record[vertex_slice.python_slice]

        # Determine how many bytes each bitfield sample will be
        num_bits = vertex_indices.count()
        sample_bytes = calc_bitfield_words(num_bits) * 4

        # Seek to start of recording memory
        region_memory.seek(4 + self._calc_indices_bytes(vertex_slice))

        # Read data from memory
        data = region_memory.read(sample_bytes * self.simulation_ticks)

        # Load into numpt
        data = np.fromstring(data, dtype=np.uint8)

        # Swap endianness
        data = data.view(dtype=np.uint32).byteswap().view(dtype=np.uint8)

        # Reverse bit order within each word
        data = np.fliplr(np.unpackbits(data).reshape(-1, 32))

        # Finally reshape into a sample shaped vector
        data = data.reshape((-1, sample_bytes * 8))

        # Loop through bits of vertex indices
        # **YUCK** this seems mega-innefficient
        spike_times = {}
        for i, b in enumerate(vertex_indices):
            # If bit is set
            if b:
                # Extract spike vector column
                vector = data[:,i]

                # Find times where neuron fired
                times = np.where(vector == 1)[0]

                # Scale these into floating point ms
                times = times.astype(np.float32, copy=False)
                times *= self.simulation_timestep_ms
                
                # Add to dictionary
                spike_times[i + vertex_slice.start] = times

        # Return dictionary of spike times
        return spike_times

    #--------------------------------------------------------------------------
    # Private API
    #--------------------------------------------------------------------------
    def _calc_indices_bytes(self, vertex_slice):
        return calc_bitfield_words(vertex_slice.slice_length) * 4
        