# Import modules
import enum
import logging
import math
import regions

# Import classes
from collections import defaultdict

# Import functions
from six import iteritems
from utils import (
    Args, create_app_ptr_and_region_files_named, sizeof_regions_named)

logger = logging.getLogger("pinus_rigida")

# ------------------------------------------------------------------------------
# Regions
# ------------------------------------------------------------------------------
class Regions(enum.IntEnum):
    """Region names, corresponding to those defined in `ensemble.h`"""
    system = 0,
    key_lookup = 1,
    synaptic_matrix = 2,
    plasticity = 3,
    output_buffer = 4,
    profiler = 5,

# ------------------------------------------------------------------------------
# SynapsePopulation
# ------------------------------------------------------------------------------
class SynapsePopulation(object):
    def __init__(self, weight_fixed_point, timer_period_us,
                 sim_ticks):
        # Calculate where the weight format fixed-point lies
        self.weight_fixed_point = weight_fixed_point
        
        # Dictionary of regions
        self.regions = {
            Regions.system:           regions.System(timer_period_us,
                                                     sim_ticks),
            Regions.key_lookup:       regions.KeyLookupBinarySearch(),
            Regions.synaptic_matrix:  regions.SynapticMatrix(),
            Regions.output_buffer:    regions.OutputBuffer(),
        }

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def partition_matrices(self, matrices, vertex_slice, in_connections):
        # Partition matrices
        sub_matrices = self.regions[Regions.synaptic_matrix].partition_matrices(
            matrices, vertex_slice, in_connections)

        # Place them in memory
        matrix_placements = self.regions[Regions.key_lookup].place_matrices(sub_matrices)

        # Return both
        return sub_matrices, matrix_placements

    def get_size(self, post_vertex_slice, sub_matrices, matrix_placements, out_buffers):
        region_arguments = self._get_region_arguments(
            post_vertex_slice, sub_matrices, matrix_placements, out_buffers)

        # Calculate region size
        vertex_size_bytes = sizeof_regions_named(self.regions, region_arguments)

        logger.debug("\t\tRegion size = %u bytes" % vertex_size_bytes)
        return vertex_size_bytes

    def write_to_file(self, post_vertex_slice, sub_matrices, matrix_placements, 
                      out_buffers, fp):
        region_arguments = self._get_region_arguments(
            post_vertex_slice, sub_matrices, matrix_placements, out_buffers)

        # Layout the slice of SDRAM we have been given
        self.region_memory = create_app_ptr_and_region_files_named(
            fp, self.regions, region_arguments)

        # Write each region into memory
        for key, region in iteritems(self.regions):
            # Get memory
            mem = self.region_memory[key]

            # Get the arguments
            args, kwargs = region_arguments[key]

            # Perform the write
            region.write_subregion_to_file(mem, *args, **kwargs)

    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _get_region_arguments(self, post_vertex_slice, sub_matrices, matrix_placements, out_buffers):
        region_arguments = defaultdict(Args)

        # Add kwargs for regions that require them
        region_arguments[Regions.system].kwargs["application_words"] =\
            [self.weight_fixed_point, post_vertex_slice.slice_length]

        region_arguments[Regions.key_lookup].kwargs["sub_matrices"] =\
            sub_matrices
        region_arguments[Regions.key_lookup].kwargs["matrix_placements"] =\
            matrix_placements
        region_arguments[Regions.synaptic_matrix].kwargs["sub_matrices"] =\
            sub_matrices
        region_arguments[Regions.synaptic_matrix].kwargs["matrix_placements"] =\
            matrix_placements
        region_arguments[Regions.synaptic_matrix].kwargs["weight_fixed_point"] =\
            self.weight_fixed_point

        region_arguments[Regions.output_buffer].kwargs["out_buffers"] =\
            out_buffers

        return region_arguments