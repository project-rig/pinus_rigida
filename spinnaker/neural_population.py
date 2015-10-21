# Import modules
import numpy as np

# Import classes
from neuron_region import NeuronRegion
from system_region import SystemRegion
from ..utils import apply_param_map

#------------------------------------------------------------------------------
# NeuralPopulation
#------------------------------------------------------------------------------
class NeuralPopulation(object):
    MAX_CELLS = 1024
    
    def __init__(self, cell_type, immutable_lazy_params, initial_values,
                 simulation_timestep_us, timer_period_us, simulation_ticks):
        # Determine number of neurons
        num_neurons = immutable_lazy_params.shape[0]

        # Use neurons mutable parameter map to
        # transform lazy array of mutable parameters
        mutable_params = apply_param_map(
            initial_values, cell_type.neuron_mutable_param_map,
            num_neurons)
        print "Mutable", mutable_params

        # Use neurons immutable parameter map to transform
        # lazy array of immutable parameters
        immutable_params = apply_param_map(
            immutable_lazy_params, cell_type.neuron_immutable_param_map,
            num_neurons)

        print "Immutable:", immutable_params

        # Use neurons
        # List of regions
        self.regions = [None] * 12
        self.regions[0] = SystemRegion(timer_period_us, simulation_ticks)
        self.regions[1] = NeuronRegion(mutable_params, immutable_params)
        #self.regions[2] = SynapseShapingRegion()
        #self.regions[6] = InputBufferRegion()
        #self.regions[8] = SpikeRecordingRegion()
        #self.regions[9] = VoltageRecordingRegion()
        #self.regions[10] = CurrentRecordingRegion()
        #self.regions[11] = ProfilerRegion()
    
    def get_size(self, vertex_slice):
        # Build formatter
        formatter = { 
            "num_application_words": 2
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
        return vertex_size_bytes
    
    def write_to_file(self, key, vertex_slice, fp):
        # Build formatter
        formatter = {
            "application_words": [key, vertex_slice.slice_length]
        }
        
        # Write regions
        for r in self.regions:
            if r is not None:
                r.write_subregion_to_file(vertex_slice, fp, **formatter)
    
    #--------------------------------------------------------------------------
    # Public methods
    #--------------------------------------------------------------------------
    '''
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
    '''