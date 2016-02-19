# Import classes
from region import Region
from rig.type_casts import NumpyFloatToFixConverter

# ------------------------------------------------------------------------------
# OutputWeight
# ------------------------------------------------------------------------------
class OutputWeight(Region):
    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self, vertex_slice, weights):
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

        # A word for each weight
        return len(vertex_slice) * 4

    def write_subregion_to_file(self, fp, vertex_slice, weights):
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
        # Convert slice of weights to fixed-point and write
        fp.write(NumpyFloatToFixConverter(signed=True, n_bits=32, n_frac=15)(
            weights[vertex_slice.python_slice]).tostring())