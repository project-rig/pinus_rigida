# Import modules
import numpy as np

# Import classes
from neuron_region import NeuronRegion
from system_region import SystemRegion

# Import functions
from utils import (
    apply_param_map, create_app_ptr_and_region_files, sizeof_regions)

#------------------------------------------------------------------------------
# NeuralPopulation
#------------------------------------------------------------------------------
class NeuralPopulation(object):
    MAX_CELLS = 1024
    
    def __init__(self, cell_type, immutable_lazy_params, initial_values,
                 simulation_timestep_us, timer_period_us, simulation_ticks):
        # Determine number of neurons
        num_neurons = immutable_lazy_params.shape[0]
        print initial_values
        # Use neurons mutable parameter map to
        # transform lazy array of mutable parameters
        mutable_params = apply_param_map(
            initial_values, cell_type.neuron_mutable_param_map,
            num_neurons)

        # Use neurons immutable parameter map to transform
        # lazy array of immutable parameters
        immutable_params = apply_param_map(
            immutable_lazy_params, cell_type.neuron_immutable_param_map,
            num_neurons)

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
    
    def get_size(self, key, vertex_slice):
        # Build region kwargs
        region_kwargs = {
            "application_words": [key, vertex_slice.slice_length]
        }
        
        # Calculate region size

        vertex_size_bytes = sizeof_regions(self.regions, vertex_slice, **region_kwargs)

        print("\tRegion size = %u bytes" % vertex_size_bytes)
        return vertex_size_bytes
    
    def write_to_file(self, key, vertex_slice, fp):
        # Build region kwargs
        region_kwargs = {
            "application_words": [key, vertex_slice.slice_length]
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