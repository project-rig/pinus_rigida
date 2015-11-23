# Import modules
import lazyarray as la
import numpy as np
import struct

# Import classes
from collections import namedtuple

# Import functions
from copy import (copy, deepcopy)
from rig.type_casts import validate_fp_params
from six import (iteritems, iterkeys)

class Args(namedtuple("Args", "args, kwargs")):
    def __new__(cls, *args, **kwargs):
        return super(Args, cls).__new__(cls, args, kwargs)

class UnitStrideSlice(namedtuple("UnitStrideSlice", ["start", "stop"])):
    @property
    def slice_length(self):
        return self.stop - self.start

    @property
    def python_slice(self):
        return slice(self.start, self.stop)

#------------------------------------------------------------------------------
# LazyArrayFloatToFixConverter
#------------------------------------------------------------------------------
class LazyArrayFloatToFixConverter(object):
    """A callable which converts a lazy array of floats to fixed point

    General usage is to create a new converter and then call this on arrays of
    values.  The `dtype` of the returned array is determined from the
    parameters passed.  For example::
        >>> f = LazyArrayFloatToFixConverter(signed=True, n_bits=8, n_frac=4)
    """
    dtypes = {
        (False, 8): np.uint8,
        (True, 8): np.int8,
        (False, 16): np.uint16,
        (True, 16): np.int16,
        (False, 32): np.uint32,
        (True, 32): np.int32,
        (False, 64): np.uint64,
        (True, 64): np.int64,
    }

    def __init__(self, signed, n_bits, n_frac, copy):
        """Create a new converter from floats into ints.

        Parameters
        ----------
        signed : bool
            Indicates that the converted values are to be signed or otherwise.
        n_bits : int
            The number of bits each value will use overall (must be 8, 16, 32,
            or 64).
        n_frac : int
            The number of fractional bits.

        copy : bool
            Should array being converted to fixed-point be deepcopied
        """
        self.min_value, self.max_value = validate_fp_params(
            signed, n_bits, n_frac)

        # Check the number of bits is sane
        if n_bits not in [8, 16, 32, 64]:
            raise ValueError(
                "n_bits: {}: Must be 8, 16, 32 or 64.".format(n_bits))

        # Store the settings
        self.bytes_per_element = n_bits / 8
        self.dtype = self.dtypes[(signed, n_bits)]
        self.n_frac = n_frac
        self.copy = copy

    def __call__(self, values):
        """Convert the given lazy array array of values into fixed point format."""
        # Make a copy of the original lazy array
        # **YUCK** deep copy here as lazy array constructor doesn't give the
        # option to copy and hence doesn't deep copy operations
        vals = deepcopy(values) if self.copy else copy(values)

        # Saturate the values
        # **TODO** this needs implementing in terms of less and more
        #vals = np.clip(values, self.min_value, self.max_value)

        # Scale and round
        vals *= (2.0 ** self.n_frac)
        vals = la.rint(vals)

        # Set data type to fixed-point type and return
        vals.dtype = self.dtype
        return vals

def evenly_slice(quantity, maximum_slice_size):
     # Build lists of start and end indices of slices
    slice_starts = range(0, quantity, maximum_slice_size)
    slice_ends = [min(s + maximum_slice_size, quantity) for s in slice_starts]

    # Zip starts and ends together into list of slices and pair these with resources
    return [UnitStrideSlice(s, e) for s, e in zip(slice_starts, slice_ends)]

# **FUTUREFRONTEND** with a bit of word to add magic number
# to the start, this is common with Nengo SpiNNaker
def create_app_ptr_and_region_files_named(fp, regions, region_args):
    """Split up a file-like view of memory into smaller views, one per region,
    and write into the first region of memory the offsets to these later
    regions.

    Parameters
    ----------
    regions : {name: Region, ...}
        Map from keys to region objects.  The keys MUST support `int`, items
        from :py:class:`enum.IntEnum` are recommended.
    region_args : {name: (*args, **kwargs)}
        Map from keys to the arguments and keyword-arguments that should be
        used when determining the size of a region.

    Returns
    -------
    {name: file-like}
        Map from region name to file-like view of memory.
    """
    # Determine the number of entries needed in the application pointer table
    ptr_len = max(int(k) for k in iterkeys(regions)) + 1

    # Construct an empty pointer table of the correct length
    ptrs = [0] * ptr_len

    # Update the offset and then begin to allocate memory
    region_memory = dict()
    offset = (ptr_len * 4) + 4  # 1 word per region and magic number
    for k, region in iteritems(regions):
        # Get the size of this region
        args, kwargs = region_args[k]
        region_size = region.sizeof_padded(*args, **kwargs)

        # Store the current offset as the pointer for this region
        ptrs[int(k)] = offset

        # Get the memory region and update the offset
        next_offset = offset + region_size
        region_memory[k] = fp[offset:next_offset]
        offset = next_offset

    # Write the pointer table into memory
    fp.seek(0)
    fp.write(struct.pack("<{}I".format(1 + ptr_len), 0xAD130AD6, *ptrs))
    fp.seek(0)

    # Return the region memories
    return region_memory

def sizeof_regions_named(regions, region_args, include_app_ptr=True):
    """Return the total amount of memory required to represent all regions when
    padded to a whole number of words each.

    Parameters
    ----------
    regions : {name: Region, ...}
        Map from keys to region objects.  The keys MUST support `int`, items
        from :py:class:`enum.IntEnum` are recommended.
    region_args : {name: (*args, **kwargs)}
        Map from keys to the arguments and keyword-arguments that should be
        used when determining the size of a region.
    """
    if include_app_ptr:
        # Get the size of the application pointer
        size = 4 + ((max(int(k) for k in iterkeys(regions)) + 1) * 4)
    else:
        # Don't include the application pointer
        size = 0

    # Get the size of all the regions
    for key, region in iteritems(regions):
        # Get the arguments for the region
        args, kwargs = region_args[key]

        # Add the size of the region
        size += region.sizeof_padded(*args, **kwargs)

    return size