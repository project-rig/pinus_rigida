# Import modules
import enum
import numpy as np
import regions

# Import classes
from collections import defaultdict

# Import functions
from utils import (
    Args, create_app_ptr_and_region_files_named, sizeof_regions_named)

#------------------------------------------------------------------------------
# NeuralPopulationRegions
#------------------------------------------------------------------------------
class NeuralPopulationRegions(enum.IntEnum):
    """Region names, corresponding to those defined in `ensemble.h`"""
    system = 0,
    neuron = 1,
    synapse = 2,
    input_buffer = 6,
    spike_recording = 8

#------------------------------------------------------------------------------
# NeuralPopulation
#------------------------------------------------------------------------------
class NeuralPopulation(object):
    MAX_CELLS = 1024
    
    def __init__(self, cell_type, parameters, initial_values,
                 simulation_timestep_us, timer_period_us, simulation_ticks,
                 indices_to_record):
        # Dictionary of regions
        self.regions = {}
        self.regions[NeuralPopulationRegions.system] =\
            regions.System(timer_period_us, simulation_ticks)
        self.regions[NeuralPopulationRegions.neuron] =\
            regions.Neuron(cell_type, parameters, initial_values)
        self.regions[NeuralPopulationRegions.synapse] =\
            regions.Synapse(cell_type, parameters, initial_values)
        self.regions[NeuralPopulationRegions.input_buffer] =\
            regions.InputBuffer()
        self.regions[NeuralPopulationRegions.spike_recording] =\
            regions.SpikeRecording(indices_to_record, simulation_ticks)
        #self.regions[9] = AnalogueRecordingRegion()
        #self.regions[10] = ProfilerRegion()
    
    #--------------------------------------------------------------------------
    # Public methods
    #--------------------------------------------------------------------------
    def get_size(self, key, vertex_slice, in_buffers):
        region_arguments = self._get_region_arguments(key, vertex_slice, in_buffers)
        
        # Calculate region size
        vertex_size_bytes = sizeof_regions_named(self.regions, region_arguments)

        print("\tRegion size = %u bytes" % vertex_size_bytes)
        return vertex_size_bytes
    
    def write_to_file(self, key, vertex_slice, in_buffers, fp):
        region_arguments = self._get_region_arguments(key, vertex_slice, in_buffers)
        
        # Layout the slice of SDRAM we have been given
        self.region_memory = create_app_ptr_and_region_files_named(
                fp, self.regions, region_arguments)

        # Write each region into memory
        for key in NeuralPopulationRegions:
            # Get the arguments and the memory
            args, kwargs = region_arguments[key]
            mem = self.region_memory[key]

            # Get the region
            region = self.regions[key]

            # Perform the write
            region.write_subregion_to_file(mem, *args, **kwargs)

    #--------------------------------------------------------------------------
    # Private methods
    #--------------------------------------------------------------------------
    def _get_region_arguments(self, key, vertex_slice, in_buffers):
        region_arguments = defaultdict(Args)

        # Add vertex slice to regions that require it
        for r in (NeuralPopulationRegions.neuron,
                  NeuralPopulationRegions.synapse,
                  NeuralPopulationRegions.spike_recording):
            region_arguments[r] = Args(vertex_slice)

        # Add kwargs for regions that require them
        region_arguments[NeuralPopulationRegions.system].kwargs["application_words"] = [key, vertex_slice.slice_length]
        region_arguments[NeuralPopulationRegions.input_buffer].kwargs["in_buffers"] = in_buffers

        return region_arguments