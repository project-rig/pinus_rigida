# Import modules
import struct

# Import classes
from rig_cpp_common.regions import Region


# ------------------------------------------------------------------------------
# OutputBuffer
# ------------------------------------------------------------------------------
class OutputBuffer(Region):
    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self, out_buffers):
        """Get the size requirements of the region in bytes.

        Parameters
        ----------
        out_buffers : list
            Contains pointers to the two output buffer memory regions

        Returns
        -------
        int
            The number of bytes required to store the data in the given slice
            of the region.
        """
        # Two pointers
        return 2 * 4

    def write_subregion_to_file(self, fp, out_buffers):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        out_buffers : list
            Contains pointers to the two output buffer memory regions
        """
        assert len(out_buffers) == 2

        # Write output buffer pointers to file
        fp.write(struct.pack("II", *out_buffers))
