# Import modules
import struct

# Import classes
from region import Region


# ------------------------------------------------------------------------------
# Flush
# ------------------------------------------------------------------------------
class Flush(Region):
    def __init__(self, flush_time):
        self.flush_time = flush_time

    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self):
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
        # Flush time
        return 4

    def write_subregion_to_file(self, fp):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        """
        # Write data to filelike
        fp.write(struct.pack("I", self.flush_time))
