# Import modules
import numpy as np

# Import classes
from master_population_array_region import MasterPopulationArrayRegion
from neuron_region import NeuronRegion
from row_size_region import RowSizeRegion
from synaptic_matrix_region import SynapticMatrixRegion


MATRIX_DATATYPE = { 
    "names":[ "mask", "delay", "weight" ], 
    "formats":[ "bool", "u1", "float" ] 
}

#------------------------------------------------------------------------------
# NeuralPopulation
#------------------------------------------------------------------------------
class NeuralPopulation(object):
    MAX_CELLS = 256
    
    def __init__(self, cell_type, parameter_records):
        # Dictionary of synaptic matrices associated with each pre-synaptic population
        # **TODO** a matrix is required for each population per synapse-type, plastic and fixed
        self.matrices = {}
        
        # List of regions
        self.regions = [None] * 16
        #self.regions[0] = SystemRegion()
        self.regions[1] = NeuronRegion(1000, len(cell_type.receptor_types), 
                                       parameter_records)
        #self.regions[2] = SynapseRegion()
        self.regions[3] = RowSizeRegion()
        self.regions[4] = MasterPopulationArrayRegion()
        self.regions[5] = SynapticMatrixRegion()
        #self.regions[6] = PlasticityRegion()
        #self.regions[7] = SpikeRecordingRegion()
        #self.regions[8] = VoltageRecordingRegion()
        #self.regions[9] = CurrentRecordingRegion()

    def write_to_file(self, key, vertex_slice, fp):
       
        # Get optimal list of row sizes for this vertex
        row_sizes = self.regions[3].calc_row_sizes(self.matrices, vertex_slice)
        
        print "Row-sizes:", row_sizes
        
        # Get dictionary of offsets for sub-matrices
        matrix_placements = self.regions[4].calc_sub_matrix_placement(
            self.matrices, vertex_slice, row_sizes)
        
        print "Matrix placements:", matrix_placements
        
        # Build formatter
        formatter = { 
            "key": key, 
            "synapse_type_input_shifts": [1, 2], 
            "weight_scale": 4096,
            "matrices": self.matrices,
            "row_sizes": row_sizes,
            "matrix_placements": matrix_placements
        }
        
        # Calculate region size
        print("Calculating size")
        vertex_size_bytes = 0
        for i, r in enumerate(self.regions):
            if r is not None:
                region_size_bytes = r.sizeof(vertex_slice, **formatter)
                print("Region %u - %u bytes" % (i, region_size_bytes))
                
                vertex_size_bytes += region_size_bytes
        
        print("= %u bytes" % vertex_size_bytes)
        
        # **TODO** sark-allocate regions and get magical file object
        # Write regions
        for r in self.regions:
            if r is not None:
                r.write_subregion_to_file(vertex_slice, fp, **formatter)
    
    #--------------------------------------------------------------------------
    # Public methods
    #--------------------------------------------------------------------------
    def convergent_connect(self, projection, pre_indices, 
                           post_index, **parameters):
        # **TODO** assemblies
        # **TODO** multiple projections and merging

        # If there's not already a synaptic matrix 
        # Associated with pre-synaptic population
        if projection.pre not in self.matrices:
            # Get shape of connection matrix
            shape = (len(projection.pre), len(projection.post))
            
            # Add synaptic matrix to dictionary
            self.matrices[projection.pre] = np.zeros(shape, dtype=MATRIX_DATATYPE)
        
        # Quantise delay into timesteps
        quantised_delay = int(round(parameters["delay"]))

        # Set mask, weight and delay for column
        # **TODO** different matrix for each connection type
        self.matrices[projection.pre][pre_indices, post_index] = (True, quantised_delay, parameters["weight"])