

# --------------------------------------------------------------------------
# SpinnakerPopulationConfig
# --------------------------------------------------------------------------
# SpiNNaker-specific configuration options for PyNN populations
class SpinnakerPopulationConfig(object):
    def __init__(self):
        self.mean_firing_rate = 10.0
        self.num_profile_samples = None
