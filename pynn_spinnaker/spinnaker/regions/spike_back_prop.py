# Import modules
import logging
import numpy as np
import struct

# Import classes
from region import Region
from rig.bitfield import BitField

logger = logging.getLogger("pynn_spinnaker")

def get_homogeneous_key_prop(verts, field, getter):
    # Call getter on each vertice's keyspace and build set
    value_set = set(getter(v.keyspace, field=field) for v in verts)

    # Assert that set contains only one element
    assert len(value_set) == 1

    # Return THE element
    return value_set.pop()

# ------------------------------------------------------------------------------
# SpikeBackProp
# ------------------------------------------------------------------------------
class SpikeBackProp(Region):
    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self, back_prop_verts):
        """Get the size requirements of the region in bytes.

        Parameters
        ----------
        back_prop_verts : :py:func:`slice`
            A list of neuron vertices that provide back-propagation
            input to this synapse vertex

        Returns
        -------
        int
            The number of bytes required to store the data in the given slice
            of the region.
        """
        # 8 words
        return 4 * 8

    def write_subregion_to_file(self, fp, back_prop_verts):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        back_prop_verts : :py:func:`slice`
            A list of neuron vertices that provide back-propagation
            input to this synapse vertex
        """
        # If there are no back-propagation vertices, write a population
        # mask of 0x00000000 and a key of 0xFFFFFFFF ensuring
        # ensuring no incoming spikes will past initial test
        if len(back_prop_verts) == 0:
            fp.write(struct.pack("IIIIIIII", 0x00000000, 0xFFFFFFFF,
                                 0, 0, 0, 0, 0, 0))
        # Otherwise
        else:
            # Get population index and mask from back-prop vertex's bitfield
            pop_mask = get_homogeneous_key_prop(
                back_prop_verts, "population_index", BitField.get_mask)
            pop_key = get_homogeneous_key_prop(
                back_prop_verts, "population_index", BitField.get_value)

            # Extract the vertex keys from each back-prob vertex's bitfield
            vertex_mask = get_homogeneous_key_prop(
                back_prop_verts, "vertex_index", BitField.get_mask)
            vertex_keys = [b.keyspace.get_value(field="vertex_index")
                           for b in back_prop_verts]
            vertex_shift = get_homogeneous_key_prop(
                back_prop_verts, "vertex_index",
                BitField.get_location_and_length)[0]

            # Get neuron mask and check neuron id starts at bottom of bitfield
            neuron_mask = get_homogeneous_key_prop(
                back_prop_verts, "neuron_id", BitField.get_mask)
            assert get_homogeneous_key_prop(
                back_prop_verts, "neuron_id",
                BitField.get_location_and_length)[0] == 0

            # Write region
            fp.write(struct.pack(
                "IIIIIIII",
                pop_mask, pop_key,
                vertex_mask, min(vertex_keys), max(vertex_keys), vertex_shift,
                len(back_prop_verts[0].neuron_slice),
                neuron_mask))

