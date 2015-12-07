import struct
from region import Region


# ------------------------------------------------------------------------------
# System
# ------------------------------------------------------------------------------
class System(Region):
    def __init__(self, timer_period_us, simulation_ticks):
        """Create a new system region.

        Parameters
        ----------
        timer_period_us : int
            period of hardware timer in microseconds
        duration_timestep : int
            Length of simulation in terms of timer ticks
        """
        self.timer_period_us = timer_period_us
        self.simulation_ticks = simulation_ticks

    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self, application_words):
        """Get the size requirements of the region in bytes.

        Parameters
        ----------
        application_words: list
            list of words to write to application-specific
            area of system region

        Returns
        -------
        int
            The number of bytes required to store the data in the given slice
            of the region.
        """
        return 4 * (2 + len(application_words))

    def write_subregion_to_file(self, fp, application_words):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        application_words: list
            list of words to write to application-specific
            area of system region
        """
        # Write structure
        fp.write(struct.pack("%uI" % (2 + len(application_words)),
                             self.timer_period_us,
                             self.simulation_ticks,
                             *application_words))
