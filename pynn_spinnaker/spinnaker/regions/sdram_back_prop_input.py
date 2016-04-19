# Import modules
import struct

# Import classes
from region import Region


# ------------------------------------------------------------------------------
# SDRAMBackPropInput
# ------------------------------------------------------------------------------
class SDRAMBackPropInput(Region):
    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self, back_prop_in_buffers):
        """Get the size requirements of the region in bytes.

        Parameters
        ----------
        vertex_slice : :py:func:`slice`
            A slice object which indicates which rows, columns or other
            elements of the region should be included.
        back_prop_in_buffers : list of 5-tuples containing pointers to
            two memory regions, their size and start and stop neuron bits

        Returns
        -------
        int
            The number of bytes required to store the data in the given slice
            of the region.
        """
        # A count followed by five words for each buffer
        return (1 + (5 * len(back_prop_in_buffers))) * 4

    def write_subregion_to_file(self, fp, back_prop_in_buffers):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        back_prop_in_buffers : list of 5-tuples containing pointers to
            two memory regions, their size and start and stop neuron bits
        """
        # Write header
        data = b''
        data += struct.pack("I", len(back_prop_in_buffers))

        # Write each buffer entry
        for p, w, s, e in back_prop_in_buffers:
            data += struct.pack("IIIII", p[0], p[1], w, s, e)

        # Write data to filelike
        fp.write(data)
