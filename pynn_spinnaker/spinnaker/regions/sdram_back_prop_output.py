# Import modules
import struct

# Import classes
from region import Region


# ------------------------------------------------------------------------------
# SDRAMBackPropOutput
# ------------------------------------------------------------------------------
class SDRAMBackPropOutput(Region):
    def __init__(self, enabled):
        self.enabled = enabled

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
        # Enabled flag and pointer if enabled, otherwise just enabled flag
        return (3 * 4) if self.enabled else (1 * 4)

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
        # If back propagation is enabled
        if self.enabled:
            assert len(out_buffers) == 2

            # Write enabled flag followed by output buffer pointers to file
            fp.write(struct.pack("III", 1, *out_buffers))
        # Otherwise write disabled flag to file
        else:
            fp.write(struct.pack("I", 0))
