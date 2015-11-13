# Import modules
import numpy as np
import regions

# Import functions
from utils import (
    create_app_ptr_and_region_files, sizeof_regions)

#------------------------------------------------------------------------------
# NeuralPopulation
#------------------------------------------------------------------------------
class NeuralPopulation(object):
    MAX_CELLS = 1024
    
    def __init__(self, cell_type, parameters, initial_values,
                 simulation_timestep_us, timer_period_us, simulation_ticks,
                 indices_to_record):
        # List of regions
        self.regions = [None] * 12
        self.regions[0] = regions.System(timer_period_us, simulation_ticks)
        self.regions[1] = regions.Neuron(cell_type, parameters, initial_values)
        self.regions[2] = regions.Synapse(cell_type, parameters, initial_values)
        self.regions[6] = regions.InputBuffer()
        self.regions[8] = regions.SpikeRecording(indices_to_record, simulation_ticks)
        #self.regions[9] = AnalogueRecordingRegion()
        #self.regions[10] = ProfilerRegion()
    
    #--------------------------------------------------------------------------
    # Public methods
    #--------------------------------------------------------------------------
    def get_size(self, key, vertex_slice, in_buffers):
        # Build region kwargs
        region_kwargs = {
            "application_words": [key, vertex_slice.slice_length],
            "in_buffers": in_buffers
        }
        
        # Calculate region size

        vertex_size_bytes = sizeof_regions(self.regions, vertex_slice, **region_kwargs)

        print("\tRegion size = %u bytes" % vertex_size_bytes)
        return vertex_size_bytes
    
    def write_to_file(self, key, vertex_slice, in_buffers, fp):
        # Build region kwargs
        region_kwargs = {
            "application_words": [key, vertex_slice.slice_length],
            "in_buffers": in_buffers
        }
        
        # Layout the slice of SDRAM we have been given
        region_memory = create_app_ptr_and_region_files(
            fp, self.regions, vertex_slice, **region_kwargs)

        # Write in each region
        for region, mem in zip(self.regions, region_memory):
            if region is None:
                pass
            #elif region is self.output_keys_region:
            #    self.output_keys_region.write_subregion_to_file(
            #        mem, vertex.slice, cluster=vertex.cluster)
            else:
                region.write_subregion_to_file(mem, vertex_slice, **region_kwargs)