"""
Connection method classes for PyNN SpiNNaker

:copyright: Copyright 2006-2015 by the PyNN team, see AUTHORS.
:license: CeCILL, see LICENSE for details.

"""
from pyNN.connectors import (AllToAllConnector,
                             FixedProbabilityConnector,
                             FixedTotalNumberConnector,
                             OneToOneConnector,
                             FixedNumberPreConnector,
                             FixedNumberPostConnector,
                             DistanceDependentProbabilityConnector,
                             DisplacementDependentProbabilityConnector,
                             IndexBasedProbabilityConnector,
                             SmallWorldConnector,
                             FromListConnector,
                             FromFileConnector,
                             CloneConnector,
                             ArrayConnector)


# ----------------------------------------------------------------------------
# AllToAllConnector
# ----------------------------------------------------------------------------
class AllToAllConnector(AllToAllConnector):
    directly_connectable = False

    def estimate_num_synapses(self, pre_slice, post_slice,
                              pre_size, post_size):
        return len(pre_slice) * len(post_slice)


# ----------------------------------------------------------------------------
# FixedProbabilityConnector
# ----------------------------------------------------------------------------
class FixedProbabilityConnector(FixedProbabilityConnector):
    directly_connectable = False

    def estimate_num_synapses(self, pre_slice, post_slice,
                              pre_size, post_size):
        return int(round(self.p_connect * float(len(pre_slice)) *
                         float(len(post_slice))))


# ----------------------------------------------------------------------------
# OneToOneConnector
# ----------------------------------------------------------------------------
class OneToOneConnector(OneToOneConnector):
    directly_connectable = True

    def estimate_num_synapses(self, pre_slice, post_slice,
                              pre_size, post_size):
        return min(len(pre_slice), len(post_slice))


# ----------------------------------------------------------------------------
# FromListConnector
# ----------------------------------------------------------------------------
class FromListConnector(FromListConnector):
    directly_connectable = False

    def estimate_num_synapses(self, pre_slice, post_slice,
                              pre_size, post_size):
        # Extract columns of pre and post indices from connection list
        pre_indices = self.conn_list[:, 0]
        post_indices = self.conn_list[:, 1]

        # Return number of list entries which contain
        # connections in both pre and post slices
        # http://stackoverflow.com/questions/9560207/how-to-count-values-in-a-certain-range-in-a-numpy-array
        return ((pre_indices >= pre_slice.start) &
                (pre_indices < pre_slice.stop) &
                (post_indices >= post_slice.start) &
                (post_indices < post_slice.stop)).sum()

# ----------------------------------------------------------------------------
# FixedNumberPostConnector
# ----------------------------------------------------------------------------
class FixedNumberPostConnector(FixedNumberPostConnector):
    directly_connectable = False

    def estimate_num_synapses(self, pre_slice, post_slice,
                              pre_size, post_size):
        return len(pre_slice) * self.n

# ----------------------------------------------------------------------------
# FixedNumberPreConnector
# ----------------------------------------------------------------------------
class FixedNumberPreConnector(FixedNumberPreConnector):
    directly_connectable = False

    def estimate_num_synapses(self, pre_slice, post_slice,
                              pre_size, post_size):
        return self.n * len(post_slice)

# ----------------------------------------------------------------------------
# FixedTotalNumberConnector
# ----------------------------------------------------------------------------
class FixedTotalNumberConnector(FixedTotalNumberConnector):
    directly_connectable = False

    def estimate_num_synapses(self, pre_slice, post_slice,
                              pre_size, post_size):
        # How large a fraction of the full pre and post populations is this
        pre_fraction = float(len(pre_slice)) / float(pre_size)
        post_fraction = float(len(post_slice)) / float(post_size)

        # Multiply these by the total number of synapses
        return int(pre_fraction * post_fraction * float(self.n))
