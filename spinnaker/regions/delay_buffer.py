# Import modules
import math
import struct

# Import classes
from region import Region

# ------------------------------------------------------------------------------
# DelayBuffer
# ------------------------------------------------------------------------------
class DelayBuffer(Region):
    def __init__(self, max_synaptic_event_rate, sim_timestep_ms, max_delay_ms):
        # Calculate maximum delay in ticks and
        # round up to next largest power-of-two
        self.max_delay_ticks = int(math.ceil(max_delay_ms / sim_timestep_ms))
        self.max_delay_ticks = 2 ** (self.max_delay_ticks - 1).bit_length()

        # Scale synaptic event rate into timer ticks
        self.max_events_per_tick =\
            max_synaptic_event_rate * (float(sim_timestep_ms) / 1000.0)


    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self, sub_matrices):
        """Get the size requirements of the region in bytes.

        Parameters
        ----------
        sub_matrices : list of :py:class:`._SubMatrix`
            Partitioned and expanded synaptic matrix rows

        Returns
        -------
        int
            The number of bytes required to store the data in the given slice
            of the region.
        """
        # Calculate buffer size
        buffer_size = self._calc_buffer_size(sub_matrices)

        # One word for number of delay slots and buffer size,
        # followed by delay matrix
        return 8 + (4 * (self.max_delay_ticks * buffer_size))

    def write_subregion_to_file(self, fp, sub_matrices):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        sub_matrices : list of :py:class:`._SubMatrix`
            Partitioned and expanded synaptic matrix rows
        """
        # Calculate buffer size
        buffer_size = self._calc_buffer_size(sub_matrices)

        # Write maximum delay ticks and buffer size
        fp.write(struct.pack("II", self.max_delay_ticks, buffer_size))

    def _calc_buffer_size(self, sub_matrices):
        # **TODO** is there a point to capping this?

        # Get the maximum number of columns in any sub-matrices
        max_cols = max(s.max_cols for s in sub_matrices)

        # Use this to scale events per tick into rows per tick
        return self.max_events_per_tick // max_cols