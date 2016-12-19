# Import modules
import math
import numpy as np
import struct

# Import classes
from rig_cpp_common.regions import Region
from rig.type_casts import NumpyFixToFloatConverter

# Import functions
from ..utils import calc_slice_bitfield_words


# ------------------------------------------------------------------------------
# AnalogueRecording
# ------------------------------------------------------------------------------
class AnalogueRecording(Region):
    """ Analogue recording regions are used to record single 'analogue'
    time-varying variables e.g. membrane voltages for neurons. They also
    support PyNN's options to only record a subset of neurons or record only
    on a fraction of timesteps

    Attributes
    ----------
    indices_to_record : :py:class:`~bitarray.bitarray`
        bitarray specifiying which neurons to record from

    record_ticks : integer
        How often should we record this analogue value (simulation time steps)
    """
    def __init__(self, indices_to_record, channel, record_sample_interval,
                 sim_timestep_ms, simulation_ticks):
        """"
        Parameters
        ----------
        indices_to_record : {integer : :py:class:`~bitarray.bitarray`}
            Dictionary of bitarrays specifiying which neurons to record for each
            recording channel.
        channel : integer
            Index of recording channel in cell_type.recordable
        record_sample_interval : float
            How often should we record this analogue value (milliseconds)
        sim_timestep_ms : float
            How large are simulation time steps in milliseconds
        simulation_ticks : integer
            How many time steps long is the simulation
        """
        self.indices_to_record = indices_to_record[channel]

        # Convert recording sample intervals to ticks
        self.record_sample_ticks = int(math.ceil(
            float(record_sample_interval) / float(sim_timestep_ms)))

        # Convert simulation duration into a number of these ticks
        self.record_ticks = int(math.ceil(
            float(simulation_ticks) / float(self.record_sample_ticks)))

    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
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
        #
        # Determine how many bytes are required for each neuron in slice
        indices_bytes = calc_slice_bitfield_words(vertex_slice) * 4

        # Slice out the vertex indices to record
        vertex_indices = self.indices_to_record[vertex_slice.python_slice]

        # Each sample requires one word per neuron
        sample_bytes = vertex_indices.count() * 4

        # Header word specifiying how many words are in each sample, indices
        # bit field and a sample bit field for each tick we're recording
        return 4 + indices_bytes + int(sample_bytes * self.record_ticks)

    def write_subregion_to_file(self, fp, vertex_slice):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        vertex_slice : :py:func:`slice`
            A slice object which indicnamedtupleates which rows,
            columns or other elements of the region should be included.
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        """
        # Slice out the vertex indices to record
        vertex_indices = self.indices_to_record[vertex_slice.python_slice]

        # Write record sample ticks
        fp.write(struct.pack("I", self.record_sample_ticks))

        # Write bitfield to file
        # **NOTE** as there's no neurons after this,
        # the word-aligned bits don't matter
        fp.write(vertex_indices.tobytes())

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    def read_signal(self, vertex_slice, region_memory):
        """
        Read back the time-varying 'analogue' signal from SpiNNaker
        
        Parameters
        ----------
        vertex_slice : :py:func:`slice`
            A slice object which indicates which rows, columns or other
            elements of the region should be included.
        region_memory : file-like
            File-like for reading region data from

        Returns
        -------
        {:py:class:`~pynn_spinnaker.spinnaker.utils.UnitStrideSlice`: {int: :py:class:`~numpy.ndarray`}}
            A dictionary mapping the slices associated with each underlying
            vertex of the neural cluster to a dictionary mapping neuron indices
            to time-varying analogue signal values.
        """
        # Get the indices within this vertes that were recorded
        vertex_indices = self.indices_to_record[vertex_slice.python_slice]

        # Each sample requires one word per neuron
        # If there are none i.e. no neurons in this vertex
        # are being recorded, return an empty dictionary
        sample_words = vertex_indices.count()
        if sample_words == 0:
            return {}

        # Seek to start of recording memory
        region_memory.seek(4 + (calc_slice_bitfield_words(vertex_slice) * 4))

        # Read data from memory
        data = region_memory.read(sample_words * 4 * self.record_ticks)

        # Load into numpy
        data = np.fromstring(data, dtype=np.int32)

        # Finally reshape into a sample shaped vector
        data = data.reshape((-1, sample_words))

        # Convert to fixed point
        data = NumpyFixToFloatConverter(15)(data)
        
        # Loop through bits of vertex indices
        # **YUCK** this seems mega-innefficient
        signals = {}
        c = 0
        for i, b in enumerate(vertex_indices):
            # If bit is set
            if b:
                # Extract neuron column
                vector = data[:, c]

                # Go onto next column
                c += 1

                # Add to dictionary
                signals[i + vertex_slice.start] = vector

        # Return dictionary of signals
        return signals
