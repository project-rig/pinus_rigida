# Import modules
import logging
import numpy as np

# Import classes
from region import Region

logger = logging.getLogger("pynn_spinnaker")

# ------------------------------------------------------------------------------
# SpikeBackProp
# ------------------------------------------------------------------------------
class SpikeBackProp(Region):
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
        # 8 words
        return 4 * 8

    def write_subregion_to_file(self, fp, vertex_slice):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        vertex_slice : :py:func:`slice`
            A slice object which indicates which rows, columns or other
            elements of the region should be included.
        """