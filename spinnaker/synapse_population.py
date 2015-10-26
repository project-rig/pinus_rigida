# Import classes
from key_lookup_binary_search_region import KeyLookupBinarySearchRegion
from synaptic_matrix_region import SynapticMatrixRegion
from system_region import SystemRegion

# Import functions
from utils import (
    create_app_ptr_and_region_files, sizeof_regions)

#------------------------------------------------------------------------------
# SynapsePopulation
#------------------------------------------------------------------------------
class SynapsePopulation(object):
    def __init__(self, matrices, timer_period_us, simulation_ticks):
        # Dictionary of pre-synaptic populations to expanded connection matrices
        self.matrices = matrices

        # List of regions
        self.regions = [None] * 12
        self.regions[0] = SystemRegion(timer_period_us, simulation_ticks)
        self.regions[3] = KeyLookupBinarySearchRegion()
        self.regions[4] = SynapticMatrixRegion()
        #self.regions[5] = PlasticityRegion()
        #self.regions[7] = OutputBufferRegion()
        #self.regions[11] = ProfilerRegion()

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

    def get_size(self, vertex_slice, sub_matrices, matrix_placements):
        # Build region kwargs
        region_kwargs = {
            "application_words": [],
            "sub_matrices": sub_matrices,
            "matrix_placements": matrix_placements
        }

        # Calculate region size
        vertex_size_bytes = sizeof_regions(self.regions, vertex_slice, **region_kwargs)

        print("\tRegion size = %u bytes" % vertex_size_bytes)
        return vertex_size_bytes

    def write_to_file(self, vertex_slice, sub_matrices, matrix_placements, fp):
        # Build region kwargs
        region_kwargs = {
            "application_words": [],
            "sub_matrices": sub_matrices,
            "matrix_placements": matrix_placements
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