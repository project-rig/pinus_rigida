# Import modules
import enum
import logging
import math
import regions

# Import classes
from collections import defaultdict

# Import functions
from utils import (
    Args, create_app_ptr_and_region_files_named, sizeof_regions_named)

logger = logging.getLogger("pinus_rigida")

#------------------------------------------------------------------------------
# SynapsePopulationRegions
#------------------------------------------------------------------------------
class SynapsePopulationRegions(enum.IntEnum):
    """Region names, corresponding to those defined in `ensemble.h`"""
    system = 0,
    key_lookup = 3,
    synaptic_matrix = 4,
    output_buffer = 7

#------------------------------------------------------------------------------
# SynapsePopulation
#------------------------------------------------------------------------------
class SynapsePopulation(object):
    def __init__(self, incoming_weight_range, timer_period_us,
                 sim_ticks):
        # Get MSB of minimum and maximum weight and get magnitude of range
        weight_msb = [math.floor(math.log(r, 2)) + 1 
                      for r in incoming_weight_range]
        weight_range = weight_msb[1] - weight_msb[0]
        
        # Check there's enough bits to represent this is any form
        assert weight_range < 16
        
        # Calculate where the weight format fixed-point lies
        self.weight_fixed_point = 16 - int(weight_msb[1])
        
        # Dictionary of regions
        self.regions = {}
        self.regions[SynapsePopulationRegions.system] =\
            regions.System(timer_period_us, sim_ticks)
        self.regions[SynapsePopulationRegions.key_lookup] =\
            regions.KeyLookupBinarySearch()
        self.regions[SynapsePopulationRegions.synaptic_matrix] =\
            regions.SynapticMatrix()
        #self.regions[5] = regions.Plasticity()
        self.regions[SynapsePopulationRegions.output_buffer] =\
            regions.OutputBuffer()
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
        region_arguments = self._get_region_arguments(
            post_vertex_slice, sub_matrices, matrix_placements, out_buffers)

        # Calculate region size
        vertex_size_bytes = sizeof_regions_named(self.regions, region_arguments)

        logger.debug("\tRegion size = %u bytes" % vertex_size_bytes)
        return vertex_size_bytes

    def write_to_file(self, post_vertex_slice, sub_matrices, matrix_placements, 
                      out_buffers, fp):
        region_arguments = self._get_region_arguments(
            post_vertex_slice, sub_matrices, matrix_placements, out_buffers)

        # Layout the slice of SDRAM we have been given
        self.region_memory = create_app_ptr_and_region_files_named(
            fp, self.regions, region_arguments)

        # Write each region into memory
        for key in SynapsePopulationRegions:
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
    def _get_region_arguments(self, post_vertex_slice, sub_matrices, matrix_placements, out_buffers):
        region_arguments = defaultdict(Args)

        # Add kwargs for regions that require them
        region_arguments[SynapsePopulationRegions.system].kwargs["application_words"] = [self.weight_fixed_point, post_vertex_slice.slice_length]

        region_arguments[SynapsePopulationRegions.key_lookup].kwargs["sub_matrices"] = sub_matrices
        region_arguments[SynapsePopulationRegions.key_lookup].kwargs["matrix_placements"] = matrix_placements

        region_arguments[SynapsePopulationRegions.synaptic_matrix].kwargs["sub_matrices"] = sub_matrices
        region_arguments[SynapsePopulationRegions.synaptic_matrix].kwargs["matrix_placements"] = matrix_placements
        region_arguments[SynapsePopulationRegions.synaptic_matrix].kwargs["weight_fixed_point"] = self.weight_fixed_point

        region_arguments[SynapsePopulationRegions.output_buffer].kwargs["out_buffers"] = out_buffers

        return region_arguments