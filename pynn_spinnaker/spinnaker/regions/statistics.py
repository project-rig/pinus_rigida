# Import modules
import logging
import struct

# Import classes
from region import Region

logger = logging.getLogger("pynn_spinnaker")

# ------------------------------------------------------------------------------
# Statistics
# ------------------------------------------------------------------------------
class Statistics(Region):
    def __init__(self, n_statistics):
        self.n_statistics = n_statistics

    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self):
        """Get the size requirements of the region in bytes.

        Returns
        -------
        int
            The number of bytes required to store the data in the given slice
            of the region.
        """
        # 1 word per sample
        return (4 * self.n_statistics)

    def write_subregion_to_file(self, fp):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        """
        pass

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    def read_stats(self, region_memory):
        # Seek to start
        region_memory.seek(0)

        # Read statistics and return
        return struct.unpack("%uI" % self.n_statistics,
                             region_memory.read(self.n_statistics * 4))
