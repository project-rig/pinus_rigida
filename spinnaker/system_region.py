import struct
from rig.regions.region import Region

RECORD_SPIKE_HISTORY  = (1 << 0)
RECORD_VOLTAGE        = (1 << 1)
RECORD_GSYN           = (1 << 2)

#------------------------------------------------------------------------------
# SystemRegion
#------------------------------------------------------------------------------
class SystemRegion(Region):
    def __init__(self, hardware_timestep_us, duration_timestep, 
                spike_recording_region_size=0, voltage_recording_region_size=0, 
                gsyn_recording_region_size=0, num_profiling_samples=0):
        """Create a new system region.

        Parameters
        ----------
        hardware_timestep_us : int
            period of hardware timer in microseconds
        duration_timestep : int
            Length of simulation in terms of timer ticks
        spike_recording_region_size : int
            Bytes of memory allocated for spike recording (if this is zero, 
            the spike recording bit is also cleared in system word)
        voltage_recording_region_size : int
            Bytes of memory allocated for neuron voltage recording (if this is
            zero, the corresponding bit is also cleared in system word)
        gsyn_recording_region_size : int
            Bytes of memory allocated for neuron gsyn recording (if this is
            zero, the corresponding bit is also cleared in system word)
        num_profiling_samples : int
            ss
        """
        self.hardware_timestep_us = hardware_timestep_us
        self.duration_timestep = duration_timestep
        self.spike_recording_region_size = spike_recording_region_size
        self.voltage_recording_region_size = voltage_recording_region_size
        self.gsyn_recording_region_size = gsyn_recording_region_size
        self.num_profiling_samples = num_profiling_samples
    
    #--------------------------------------------------------------------------
    # Region methods
    #--------------------------------------------------------------------------
    def sizeof(self, vertex_slice, **formatter_args):
        """Get the size requirements of the region in bytes.

        Parameters
        ----------
        vertex_slice : :py:func:`slice`
            A slice object which indicates which rows, columns or other
            elements of the region should be included.
        formatter_args : optional
            Arguments which will be passed to the (optional) formatter along
            with each value that is being written.
            
        Returns
        -------
        int
            The number of bytes required to store the data in the given slice
            of the region.
        """
         # Region is always an 8 word struct
        return 4 * 8

    def write_subregion_to_file(self, vertex_slice, fp, **formatter_args):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        vertex_slice : :py:func:`slice`
            A slice object which indicates which rows, columns or other
            elements of the region should be included.
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        formatter_args : optional
            Arguments which will be passed to the (optional) formatter along
            with each value that is being written.
        """
        # Build system word
        system_word = 0
        if self.spike_recording_region_size > 0:
            system_word |= RECORD_SPIKE_HISTORY
        if self.voltage_recording_region_size > 0:
            system_word |= RECORD_VOLTAGE
        if self.gsyn_recording_region_size > 0:
            system_word |= RECORD_GSYN
        
        # Write structure
        fp.write(struct.pack("IIIIIIII", 
            0,                                  # **NOTE** unused app-id
            self.hardware_timestep_us,
            self.duration_timestep,
            system_word,
            self.spike_recording_region_size,
            self.voltage_recording_region_size,
            self.gsyn_recording_region_size,
            self.num_profiling_samples))