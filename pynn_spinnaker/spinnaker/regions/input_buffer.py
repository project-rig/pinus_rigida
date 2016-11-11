# Import modules
import struct

# Import classes
from rig_cpp_common.regions import Region

# ------------------------------------------------------------------------------
# InputBuffer
# ------------------------------------------------------------------------------
class InputBuffer(Region):
    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self, in_buffers):
        """Get the size requirements of the region in bytes.

        Parameters
        ----------
        vertex_slice : :py:func:`slice`
            A slice object which indicates which rows, columns or other
            elements of the region should be included.
        in_buffers : list of 5-tuples containing pointers to
            two memory regions, index of start neuron, number of neurons,
            receptor index and fixed-point format

        Returns
        -------
        int
            The number of bytes required to store the data in the given slice
            of the region.
        """
        # A count followed by 6 words for each buffer
        return (1 + (6 * len(in_buffers))) * 4

    def write_subregion_to_file(self, fp, in_buffers):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        vertex_slice : :py:func:`slice`
            A slice object which indicnamedtupleates which rows,
            columns or other elements of the region should be included.
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        in_buffers : list of 5-tuples containing pointers to
            two memory regions, index of start neuron, number of neurons,
            receptor index and fixed-point format
        """
        # Write header
        data = b''
        data += struct.pack("I", len(in_buffers))

        # Write each buffer entry
        for b in in_buffers:
            data += struct.pack("IIIIIi", b.pointers[0], b.pointers[1],
                                b.start_neuron, b.num_neurons,
                                b.receptor_index, 15 - b.weight_fixed_point)

        # Write data to filelike
        fp.write(data)
