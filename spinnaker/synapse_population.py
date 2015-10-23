# Import classes
from master_population_array_region import MasterPopulationArrayRegion
from row_size_region import RowSizeRegion
from synaptic_matrix_region import SynapticMatrixRegion
from system_region import SystemRegion

#MATRIX_DATATYPE = {
#    "names":[ "mask", "delay", "weight" ],
#    "formats":[ "bool", "u1", "float" ]
#}


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
        #self.regions[3] = KeyLookupRegion()
        #self.regions[4] = SynapticMatrixRegion()
        #self.regions[5] = PlasticityRegion()
        #self.regions[7] = OutputBufferRegion()
        #self.regions[11] = ProfilerRegion()

    #--------------------------------------------------------------------------
    # Public methods
    #--------------------------------------------------------------------------
    def get_size(self, key, vertex_slice):
        # Build region kwargs
        region_kwargs = {
            "application_words": []
        }

        # Calculate region size
        vertex_size_bytes = sizeof_regions(self.regions, vertex_slice, **region_kwargs)

        print("\tRegion size = %u bytes" % vertex_size_bytes)
        return vertex_size_bytes

    def write_to_file(self, key, vertex_slice, fp):
        # Build region kwargs
        region_kwargs = {
            "application_words": []
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