# Import modules
import math
import regions

# Import functions
from utils import (
    create_app_ptr_and_region_files, sizeof_regions)

#------------------------------------------------------------------------------
# SynapsePopulation
#------------------------------------------------------------------------------
class SynapsePopulation(object):
    def __init__(self, matrices, incoming_weight_range, timer_period_us, 
                 simulation_ticks):
        self.matrices = matrices
        #self.incoming_weight_range = incoming_weight_range
        
        # Get MSB of minimum and maximum weight and get magnitude of range
        weight_msb = [math.floor(math.log(r, 2)) + 1 
                      for r in incoming_weight_range]
        weight_range = weight_msb[1] - weight_msb[0]
        
        # Check there's enough bits to represent this is any form
        assert weight_range < 16
        
        # Calculate where the weight format fixed-point lies
        self.weight_fixed_point = 16 - int(weight_msb[1])
        
        # List of regions
        self.regions = [None] * 12
        self.regions[0] = regions.System(timer_period_us, simulation_ticks)
        self.regions[3] = regions.KeyLookupBinarySearch()
        self.regions[4] = regions.SynapticMatrix()
        #self.regions[5] = regions.Plasticity()
        self.regions[7] = regions.OutputBuffer()
        #self.regions[10] = regions.Profiler()

    #--------------------------------------------------------------------------
    # Public methods
    #--------------------------------------------------------------------------
    def partition_matrices(self, matrices, vertex_slice, incoming_connections):
        # Partition matrices
        sub_matrices = self.regions[4].partition_matrices(
            matrices, vertex_slice, incoming_connections)

        # Place them in memory
        matrix_placements = self.regions[3].place_matrices(sub_matrices)

        # Return both
        return sub_matrices, matrix_placements

    def get_size(self, post_vertex_slice, sub_matrices, matrix_placements, out_buffers):
        # Build region kwargs
        region_kwargs = {
            "application_words": [self.weight_fixed_point, 
                                  post_vertex_slice.slice_length],
            "sub_matrices": sub_matrices,
            "matrix_placements": matrix_placements,
            "out_buffers": out_buffers,
            "weight_fixed_point": self.weight_fixed_point
        }

        # Calculate region size
        vertex_size_bytes = sizeof_regions(self.regions, post_vertex_slice, 
                                           **region_kwargs)

        print("\tRegion size = %u bytes" % vertex_size_bytes)
        return vertex_size_bytes

    def write_to_file(self, post_vertex_slice, sub_matrices, matrix_placements, 
                      out_buffers, fp):
        # Build region kwargs
        region_kwargs = {
            "application_words": [self.weight_fixed_point, 
                                  post_vertex_slice.slice_length],
            "sub_matrices": sub_matrices,
            "matrix_placements": matrix_placements,
            "out_buffers": out_buffers,
            "weight_fixed_point": self.weight_fixed_point
        }

        # Layout the slice of SDRAM we have been given
        region_memory = create_app_ptr_and_region_files(
            fp, self.regions, post_vertex_slice, **region_kwargs)

        # Write in each region
        for region, mem in zip(self.regions, region_memory):
            if region is None:
                pass
            #elif region is self.output_keys_region:
            #    self.output_keys_region.write_subregion_to_file(
            #        mem, vertex.slice, cluster=vertex.cluster)
            else:
                region.write_subregion_to_file(mem, post_vertex_slice, 
                                               **region_kwargs)