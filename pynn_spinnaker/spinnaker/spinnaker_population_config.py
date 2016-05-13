

# --------------------------------------------------------------------------
# SpinnakerPopulationConfig
# --------------------------------------------------------------------------
# SpiNNaker-specific configuration options for PyNN populations
class SpinnakerPopulationConfig(object):
    def __init__(self):
        self.mean_firing_rate = 10.0
        self.num_profile_samples = None
        self.max_neurons_per_core = None
        self.max_cluster_width = None
        self.flush_time = None
