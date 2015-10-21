# Import modules
import numpy as np

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