
# Import modules
import numpy as np
import struct

# Import classes
from collections import namedtuple

class UnitStrideSlice(namedtuple("UnitStrideSlice", ["start", "stop"])):
    @property
    def slice_length(self):
        return self.stop - self.start

    @property
    def python_slice(self):
        return slice(self.start, self.stop)

def evenly_slice(quantity, maximum_slice_size):
     # Build lists of start and end indices of slices
    slice_starts = range(0, quantity, maximum_slice_size)
    slice_ends = [min(s + maximum_slice_size, quantity) for s in slice_starts]

    # Zip starts and ends together into list of slices and pair these with resources
    return [UnitStrideSlice(s, e) for s, e in zip(slice_starts, slice_ends)]

def apply_param_map(lazy_params, param_map, size):
    # Build numpy record datatype for neuron region
    # **TODO** this probably doesn't need to be a string - could use np.uint8 style things throughout
    record_datatype = ",".join(zip(*param_map)[1])

    # Build a numpy record array large enough for all neurons
    params = np.empty(size, dtype=(record_datatype))

    # Loop through parameters
    for f, n in zip(params.dtype.names, param_map):
        # If this map entry has a constant value,
        # Write it into field for all neurons
        if len(n) == 2:
            params[f][:] = n[0]
        # Otherwise
        else:
            assert len(n) == 3

            # Apply translation function to parameter and write into field
            params[f] = n[2](lazy_params[n[0]].evaluate())

    return params

# **FUTUREFRONTEND** with a bit of word to add magic number
# to the start, this is common with Nengo SpiNNaker
def create_app_ptr_and_region_files(fp, regions, vertex_slice, **kwargs):
    """Split up a file-like view of memory into smaller views, one per region,
    and write into the first region of memory the offsets to these later
    regions.

    Returns
    -------
    [file-like view, ...]
        A file-like view of memory for each region.
    """
    # First we split off the application pointer region
    ptrs = [0 for n in range(len(regions) + 1)]
    offset = 4 + len(ptrs)*4  # 1 word per region and magic number

    # Then we go through and assign each region in turn
    region_memory = list()
    for i, r in enumerate(regions, start=1):
        if r is None:
            region_memory.append(None)
        else:
            ptrs[i] = offset
            next_offset = offset + r.sizeof_padded(vertex_slice, **kwargs)
            region_memory.append(fp[offset:next_offset])
            offset = next_offset

    # Write magic number followed by pointer table
    fp.seek(0)
    fp.write(struct.pack("<%uI" % (1 + len(ptrs)), 0xAD130AD6, *ptrs))

    # Return the file views
    return region_memory

# **FUTUREFRONTEND** this is common with Nengo SpiNNaker
def sizeof_regions(regions, vertex_slice, include_app_ptr=True, **kwargs):
    """Return the total amount of memory required to represent all the regions
    when they are padded to take a whole number of words each.
    """
    size = sum(r.sizeof_padded(vertex_slice, **kwargs) for r in regions if r is not None)
    if include_app_ptr:
        size += (len(regions) * 4) + 4
    return size