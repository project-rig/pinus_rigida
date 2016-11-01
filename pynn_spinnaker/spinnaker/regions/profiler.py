# Import modules
import logging
import numpy as np
import struct

# Import classes
from region import Region

MS_SCALE = (1.0 / 200032.4)

logger = logging.getLogger("pynn_spinnaker")


# ------------------------------------------------------------------------------
# Profiler
# ------------------------------------------------------------------------------
class Profiler(Region):
    def __init__(self, n_samples):
        self.n_samples = n_samples

    # --------------------------------------------------------------------------
    # Region methods
    # --------------------------------------------------------------------------
    def sizeof(self):
        """Get the size requirements of the region in bytes.

        Returns
        -------
        int
            The number of bytes required to store the data in the given slice
            of the region.
        """
        # 2 word counters and 2 words per sample
        return 8 + int(8 * self.n_samples)

    def write_subregion_to_file(self, fp):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        """
        # Write number of samples supported
        fp.write(struct.pack("I", self.n_samples))

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    def read_profile(self, region_memory, tag_names):
        # Seek past number of samples
        region_memory.seek(4)

        # Read number of words written by profiler
        word_written = struct.unpack("I", region_memory.read(4))[0]

        # Read these from memory
        data = np.fromstring(region_memory.read(word_written * 4),
                             dtype=np.uint32)
        assert len(data) % 2 == 0

        # Slice data into seperate times, tags and flags
        sample_times = data[::2]
        sample_tags_and_flags = data[1::2]

        # Further split the tags and flags word
        # into seperate arrays        # of tags and flags
        sample_tags = np.bitwise_and(sample_tags_and_flags, 0x7FFFFFFF)
        sample_flags = np.right_shift(sample_tags_and_flags, 31)

        # Find indices of samples relating to entries and exits
        sample_entry_indices = np.where(sample_flags == 1)
        sample_exit_indices = np.where(sample_flags == 0)

        # Convert count-down times to count up times from 1st sample
        sample_times = np.subtract(sample_times[0], sample_times)
        sample_times = np.multiply(sample_times, MS_SCALE, dtype=np.float)

        # Slice tags and times into entry and exits
        entry_tags = sample_tags[sample_entry_indices]
        entry_times = sample_times[sample_entry_indices]
        exit_tags = sample_tags[sample_exit_indices]
        exit_times = sample_times[sample_exit_indices]

        # Loop through unique tags
        tag_dictionary = dict()
        unique_tags = np.unique(sample_tags)
        for tag in unique_tags:
            # Check we have a name for this tag
            assert tag in tag_names

            # Get indices where these tags occur
            tag_entry_indices = np.where(entry_tags == tag)
            tag_exit_indices = np.where(exit_tags == tag)

            # Use these to get subset for this tag
            tag_entry_times = entry_times[tag_entry_indices]
            tag_exit_times = exit_times[tag_exit_indices]

            # If both these subsets aren't empty
            if len(tag_entry_times) > 0 and len(tag_exit_times) > 0:
                # If there is one more entry tags than exit tag
                # (we assume they aren't ever nested)
                if len(tag_entry_times) == (len(tag_exit_times) + 1):
                    num_trim_tags = len(tag_entry_times) - len(tag_exit_times)
                    logger.warn("Profile finishes with tag %s "
                                "open - trimming %u tags",
                                tag_names[tag], num_trim_tags)
                    tag_entry_times = tag_entry_times[:-num_trim_tags]

                # If number of entry and exit tags still don't match something
                # Has probably crashed early so the profiling data is useless
                if len(tag_entry_times) != len(tag_exit_times):
                    logger.error("Tag %s broken:", tag_names[tag])
                # Otherwise
                else:
                    # Subtract entry times from exit times
                    # to get durations of each call
                    tag_durations = np.subtract(tag_exit_times,
                                                tag_entry_times)

                    # Add entry times and durations to dictionary
                    tag_dictionary[tag_names[tag]] = (
                        tag_entry_times, tag_durations)

        return tag_dictionary
