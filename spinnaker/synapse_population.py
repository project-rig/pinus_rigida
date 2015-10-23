# Import classes
from collections import namedtuple
from master_population_array_region import MasterPopulationArrayRegion
from row_size_region import RowSizeRegion
from synaptic_matrix_region import SynapticMatrixRegion
from system_region import SystemRegion

#MATRIX_DATATYPE = {
#    "names":[ "mask", "delay", "weight" ],
#    "formats":[ "bool", "u1", "float" ]
#}

Synapse = namedtuple("Synapse", ["weight", "delay", "index"])

#------------------------------------------------------------------------------
# SynapsePopulation
#------------------------------------------------------------------------------
class SynapsePopulation(object):
    def __init__(self):
        # Dictionary of pre-synaptic populations to matrices
        self.matrices = {}

    #--------------------------------------------------------------------------
    # Public methods
    #--------------------------------------------------------------------------
    def convergent_connect(self, projection, pre_indices,
                           post_index, matrix_rows, **parameters):
        # Add synapse to each row
        for p in matrix_rows[pre_indices]:
            p.append(Synapse(parameters["weight"], parameters["delay"], post_index))