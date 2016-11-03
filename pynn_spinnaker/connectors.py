"""
Connection method classes for PyNN SpiNNaker

:copyright: Copyright 2006-2015 by the PyNN team, see AUTHORS.
:license: CeCILL, see LICENSE for details.

"""
# Import modules
import numpy as np
import scipy
from spinnaker import lazy_param_map
import lazyarray as la

# Import classes
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

def _draw_hypergeom(context, **kwargs):
    sample = np.random.hypergeometric(ngood = context['n'],
                                 nbad = context['N'] - context['n'],
                                 nsample = context['nsample'])
    context['n'] -= sample
    context['N'] -= context['nsample']
    return la.larray(sample, shape=(1,))

# ----------------------------------------------------------------------------
# AllToAllConnector
# ----------------------------------------------------------------------------
class AllToAllConnector(AllToAllConnector):
    # Can suitable populations connected with this connector be connected
    # using an in-memory buffer rather than by sending multicast packets
    _directly_connectable = False

    # If this connector can be generated on chip, parameter map to use
    _on_chip_param_map = [("allow_self_connections", "u4", lazy_param_map.u032)]

    # --------------------------------------------------------------------------
    # Internal SpiNNaker methods
    # --------------------------------------------------------------------------
    def _estimate_max_row_synapses(self, pre_slice, post_slice,
                                   pre_size, post_size):
        return len(post_slice)

    def _estimate_num_synapses(self, pre_slice, post_slice,
                               pre_size, post_size):
        return len(pre_slice) * len(post_slice)

    def _get_projection_initial_state(self, pre_size, post_size):
        return None


# ----------------------------------------------------------------------------
# FixedProbabilityConnector
# ----------------------------------------------------------------------------
class FixedProbabilityConnector(FixedProbabilityConnector):
    # Can suitable populations connected with this connector be connected
    # using an in-memory buffer rather than by sending multicast packets
    _directly_connectable = False

    # If this connector can be generated on chip, parameter map to use
    _on_chip_param_map = [("p_connect", "u4", lazy_param_map.u032),
                          ("allow_self_connections", "u4", lazy_param_map.u032)]

    # --------------------------------------------------------------------------
    # Internal SpiNNaker methods
    # --------------------------------------------------------------------------
    def _estimate_max_row_synapses(self, pre_slice, post_slice,
                                   pre_size, post_size):
        # Each connection is made with probability p_connect
        # Return the row-length that 99.99% of rows will be shorter than
        return int(scipy.stats.binom.ppf(
            0.9999, len(post_slice), self.p_connect))

    def _estimate_num_synapses(self, pre_slice, post_slice,
                               pre_size, post_size):
        return int(round(self.p_connect * float(len(pre_slice)) *
                         float(len(post_slice))))

    def _get_projection_initial_state(self, pre_size, post_size):
        return None


# ----------------------------------------------------------------------------
# OneToOneConnector
# ----------------------------------------------------------------------------
class OneToOneConnector(OneToOneConnector):
    # Can suitable populations connected with this connector be connected
    # using an in-memory buffer rather than by sending multicast packets
    _directly_connectable = True

    # --------------------------------------------------------------------------
    # Internal SpiNNaker methods
    # --------------------------------------------------------------------------
    def _estimate_max_row_synapses(self, pre_slice, post_slice,
                                   pre_size, post_size):
        return 1 if pre_slice.overlaps(post_slice) else 0

    def _estimate_num_synapses(self, pre_slice, post_slice,
                               pre_size, post_size):
        return min(len(pre_slice), len(post_slice))

    def _get_projection_initial_state(self, pre_size, post_size):
        return None


# ----------------------------------------------------------------------------
# FromListConnector
# ----------------------------------------------------------------------------
class FromListConnector(FromListConnector):
    # Can suitable populations connected with this connector be connected
    # using an in-memory buffer rather than by sending multicast packets
    _directly_connectable = False

    # --------------------------------------------------------------------------
    # Internal SpiNNaker methods
    # --------------------------------------------------------------------------
    def _estimate_max_row_synapses(self, pre_slice, post_slice,
                                   pre_size, post_size):
        # Extract columns of pre and post indices from connection list
        pre_indices = self.conn_list[:, 0]
        post_indices = self.conn_list[:, 1]

        # Build mask to select list entries in slice
        mask = ((pre_indices >= pre_slice.start) &
                (pre_indices < pre_slice.stop) &
                (post_indices >= post_slice.start) &
                (post_indices < post_slice.stop))

        # Use mask to select slice pre-indices
        slice_pre_indices = pre_indices[mask].astype(int)

        # Return maximum number of list entries in each bin
        return np.amax(np.bincount(slice_pre_indices));

    def _estimate_num_synapses(self, pre_slice, post_slice,
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

    def _get_projection_initial_state(self, pre_size, post_size):
        return None


# ----------------------------------------------------------------------------
# FixedNumberPostConnector
# ----------------------------------------------------------------------------
class FixedNumberPostConnector(FixedNumberPostConnector):
    # Can suitable populations connected with this connector be connected
    # using an in-memory buffer rather than by sending multicast packets
    _directly_connectable = False

    _on_chip_param_map = [("allow_self_connections", "u4", lazy_param_map.u032)]

    # --------------------------------------------------------------------------
    # Internal SpiNNaker methods
    # --------------------------------------------------------------------------
    def _estimate_max_row_synapses(self, pre_slice, post_slice,
                                   pre_size, post_size):
        # Each pre-synaptic neuron connects to n of the M=post_size
        # post-synaptic neurons.
        # Determining which of those n connections are within this post_slice is
        # a matter of sampling N=len(post_slice) times without replacement.
        # The number within the row and post_slice are
        # hypergeometrically distributed.

        # Return the row-length that 99.99% of rows will be shorter than
        return int(scipy.stats.hypergeom.ppf(
            0.9999, M=post_size, n=self.n, N=len(post_slice)))

    def _estimate_num_synapses(self, pre_slice, post_slice,
                               pre_size, post_size):
        # How large a fraction of the full post populations is this
        post_fraction = float(len(post_slice)) / float(post_size)

        return int(len(pre_slice) * self.n * post_fraction)

    def _get_projection_initial_state(self, pre_size, post_size):
        return None


# ----------------------------------------------------------------------------
# FixedNumberPreConnector
# ----------------------------------------------------------------------------
class FixedNumberPreConnector(FixedNumberPreConnector):
    # Can suitable populations connected with this connector be connected
    # using an in-memory buffer rather than by sending multicast packets
    _directly_connectable = False

    _on_chip_param_map = [("allow_self_connections", "u4", lazy_param_map.u032)]

    # --------------------------------------------------------------------------
    # Internal SpiNNaker methods
    # --------------------------------------------------------------------------
    def _estimate_max_row_synapses(self, pre_slice, post_slice,
                                   pre_size, post_size):
        # Calculate the probability that any of the
        # n synapses in the column will be within this row
        prob_in_row = float(self.n) / pre_size

        # Return the row-length that 99.99% of rows will be shorter than
        return int(scipy.stats.binom.ppf(
            0.9999, len(post_slice), prob_in_row))

    def _estimate_num_synapses(self, pre_slice, post_slice,
                               pre_size, post_size):
        # How large a fraction of the full pre populations is this
        pre_fraction = float(len(pre_slice)) / float(pre_size)

        return int(len(post_slice) * self.n * pre_fraction)

    def _get_projection_initial_state(self, pre_size, post_size):
        return None


# ----------------------------------------------------------------------------
# FixedTotalNumberConnector
# ----------------------------------------------------------------------------
class FixedTotalNumberConnector(FixedTotalNumberConnector):
    # Can suitable populations connected with this connector be connected
    # using an in-memory buffer rather than by sending multicast packets
    _directly_connectable = False

    _on_chip_param_map = [("allow_self_connections", "u4", lazy_param_map.u032),
                          (_draw_hypergeom, "u4")]

    # --------------------------------------------------------------------------
    # Internal SpiNNaker methods
    # --------------------------------------------------------------------------
    def _estimate_max_row_synapses(self, pre_slice, post_slice,
                                   pre_size, post_size):
        # There are n connections amongst the M=pre_size*post_size possible
        # connections.
        # Determining which of those n connections are within this row and
        # post_slice is a matter of sampling N=len(post_slice) times without
        # replacement. The number within the row and post_slice are
        # hypergeometrically distributed.

        M = pre_size * post_size
        N = len(post_slice)

        return int(scipy.stats.hypergeom.ppf(0.9999, M=M, N=N, n=self.n))

    def _estimate_num_synapses(self, pre_slice, post_slice,
                               pre_size, post_size):
        # How large a fraction of the full pre and post populations is this
        pre_fraction = float(len(pre_slice)) / float(pre_size)
        post_fraction = float(len(post_slice)) / float(post_size)

        # Multiply these by the total number of synapses
        return int(pre_fraction * post_fraction * float(self.n))

    def _get_projection_initial_state(self, pre_size, post_size):
        return {'n': self.n, 'N': pre_size * post_size}
