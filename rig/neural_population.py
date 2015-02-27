from neuron_region import NeuronRegion
from synaptic_matrix_region import SynapticMatrixRegion

#------------------------------------------------------------------------------
# NeuralPopulation
#------------------------------------------------------------------------------
class NeuralPopulation(object):
    MAX_CELLS = 256
    
    def __init__(self, cell_type, parameter_records):
        self.regions = [None] * 16
        self.regions[1] = NeuronRegion(1000, len(cell_type.receptor_types), 
                                       parameter_records)
        self.regions[5] = SynapticMatrixRegion()
    
    def convergent_connect(self, projection, presynaptic_indices, 
                           postsynaptic_index, **connection_parameters):
        # Make synaptic connections
        self.regions[5].convergent_connect(projection, 
                                           presynaptic_indices, 
                                           postsynaptic_index,
                                           **connection_parameters)
    
    def get_vertices(self):
        """Write a portion of the region to a file applying the formatter.

        Parameters
        ----------
        vertex_slice : :py:func:`slice`
            A slice object which indicates which rows, columns or other
            elements of the region should be included.
        fp : file-like object
            The file-like object to which data from the region will be written.
            This must support a `write` method.
        formatter_args : optional
            Arguments which will be passed to the (optional) formatter along
            with each value that is being written.
        """
        
        slices = [ slice(0, 10), slice(10, 20) ]
    
    def write_to_file(self, fp):
        # **TEMP** build a fake vertex
        vertex_slice = slice(0, self.regions[1].num_neurons)
        
        formatter = { "key": 0, "synapse_type_input_shifts": [1, 2], "weight_scale": 4096 }
        
        # Write regions
        for r in self.regions:
            if r is not None:
                r.write_subregion_to_file(vertex_slice, fp, **formatter)