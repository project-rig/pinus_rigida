# Import modules
import logging

# Import classes
from region import Region

# Import functions
from zlib import crc32

logger = logging.getLogger("pynn_spinnaker")

def _crc_u32(value):
    return crc32(value) & 0xFFFFFFFF

def _get_param_type_name(parameter):
    # If parameter is a random distribution
    if isinstance(parameter.base_value, RandomDistribution):
        # Assert that it uses our native RNG
        assert isinstance(parameter.base_value.rng, NativeRNG)

        # Return distribution name
        return parameter.base_value.name
    # Otherwise if it's a scalar, return the magic string constant
    elif isinstance(parameter.base_value,
                    (int, long, np.integer, float, bool)):
        return "constant"
    # Otherwise assert
    else:
        assert False:

# ------------------------------------------------------------------------------
# ConnectionBuilder
# ------------------------------------------------------------------------------
class ConnectionBuilder(Region):
    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self, vertex_slice, sub_matrix_props,
               chip_sub_matrix_projs):
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
        sub_matrix_props :
            A list of SubMatrix structures
            specifying matrices to generate on chip
        chip_sub_matrix_projs :
            A list of Projections from which to extract
            properties required to build matrices on chip
        """

        # A word for each weight
        #return 4 + (len(chip_sub_matrix_props) * )
        return 0

    def write_subregion_to_file(self, fp, vertex_slice, sub_matrix_props,
                                chip_sub_matrix_projs):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        vertex_slice : :py:func:`slice`
            A slice object which indicates which rows, columns or other
            elements of the region should be included.
        sub_matrix_props :
            A list of SubMatrix structures
        chip_sub_matrix_projs :
            A list of Projections from which to extract
            properties required to build matrices on chip
        """
        # **TODO** write RNG seed

        num_chip_matrices = len(chip_sub_matrix_projs)

        # Write number of matrices
        #fp.write(struct.pack("I", len(chip_sub_matrix_props)))

        # Loop through projections
        for prop, proj in zip(sub_matrix_props[-num_chip_matrices:], chip_sub_matrix_projs):
            # Extract required properties from projections
            synapse_type = proj.synapse_type
            connector = proj._connector

            delay = synapse_type.parameter_space["delay"]
            weight = synapse_type.parameter_space["weight"]

            logger.debug(
                "\t\t\t\t\tWriting connection builder data for projection "
                "key:%08x, synapse type:%s, connector type:%s, delay type:%s, "
                "weight type:%s", prop.key, synapse_type.__class__.__name__,
                connector.__class__.__name, _get_param_type_name(delay),
                _get_param_type_name(weight))

            #fp.write(struct.pack("IIIII", prop.key, _crc_u32()
        assert False
