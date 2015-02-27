

#------------------------------------------------------------------------------
# NeuralPopulation
#------------------------------------------------------------------------------
class NeuralPopulation(object):
    MAX_CELLS = 256
    
    def __init__(self, neuron_region):
        self.regions = [None] * 16
        self.regions[1] = neuron_region
        
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