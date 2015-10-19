from collections import namedtuple

class UnitStrideSlice(namedtuple("UnitStrideSlice", ["start", "stop"])):
    @property
    def slice_length(self):
        return self.stop - self.start

def evenly_slice(quantity, maximum_slice_size):
     # Build lists of start and end indices of slices
    slice_starts = range(0, quantity, maximum_slice_size)
    slice_ends = [min(s + maximum_slice_size, quantity) for s in slice_starts]

    # Zip starts and ends together into list of slices and pair these with resources
    return [UnitStrideSlice(s, e) for s, e in zip(slice_starts, slice_ends)]