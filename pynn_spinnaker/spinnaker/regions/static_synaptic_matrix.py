# Import modules
import logging
import numpy as np

# Import classes
from synaptic_matrix import SynapticMatrix

logger = logging.getLogger("pynn_spinnaker")



# ------------------------------------------------------------------------------
# StaticSynapticMatrix
# ------------------------------------------------------------------------------
class StaticSynapticMatrix(SynapticMatrix):
    # Static synapses are stored in single 32-bit words with the weight
    # stored in the bits above index and delay
    WeightShift = SynapticMatrix.IndexBits + SynapticMatrix.DelayBits

     # 3 header words :
     # > num synapses
     # > next delay row time
     # > next delay offset-length
    num_header_words = 3

    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _get_row_words(self, num_synapses):
        return self.num_header_words + num_synapses

    def _write_spinnaker_synapses(self, dtcm_delay, weight_fixed, indices,
                                  destination):
        destination = (indices
                       | (dtcm_delay << self.IndexBits)
                       | (weight_fixed << self.WeightShift))