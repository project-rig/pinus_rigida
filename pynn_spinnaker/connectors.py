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

from pyNN.random import RandomDistribution

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

def _draw_num_connections(context, post_slice_size, pre_slice_size, **kwargs):
    nsample = post_slice_size * pre_slice_size

    if context['n'] == 0:
        sample = 0
    elif nsample == context['N']:
        sample = context['n']
    elif context['with_replacement']:
        sample = np.random.binomial(n = context['n'],
                                    p = float(nsample) / context['N'])
    else:
        sample = np.random.hypergeometric(ngood = context['n'],
                                          nbad = context['N'] - context['n'],
                                          nsample = nsample)
    context['n'] -= sample
    context['N'] -= nsample

    return la.larray(sample, shape=(1,))

def _submat_size(context, post_slice_size, pre_slice_size, **kwargs):
    return la.larray(post_slice_size * pre_slice_size, shape=(1,))
    return la.larray(sample, shape=(1,))

# ----------------------------------------------------------------------------
# AllToAllConnector
# ----------------------------------------------------------------------------
class AllToAllConnector(AllToAllConnector):
    # Can suitable populations connected with this connector be connected
    # using an in-memory buffer rather than by sending multicast packets
    _directly_connectable = False

    # If this connector can be generated on chip, parameter map to use
    _on_chip_param_map = [("allow_self_connections", "u4", lazy_param_map.integer)]

    # --------------------------------------------------------------------------
    # Internal SpiNNaker methods
    # --------------------------------------------------------------------------
    def _estimate_max_row_synapses(self, pre_slice, post_slice,
                                   pre_size, post_size):
        return len(post_slice)

    def _estimate_mean_row_synapses(self, pre_slice, post_slice,
                                    pre_size, post_size):
        return len(post_slice)

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
    _on_chip_param_map = [("allow_self_connections", "u4", lazy_param_map.integer),
                          ("p_connect", "u4", lazy_param_map.u032)]

    # --------------------------------------------------------------------------
    # Internal SpiNNaker methods
    # --------------------------------------------------------------------------
    def _estimate_max_row_synapses(self, pre_slice, post_slice,
                                   pre_size, post_size):
        N = len(post_slice)
        M = pre_size * post_size

        # If scipy.stats.<dist>.ppf(p, **params) gives the (100*p)th percentile of
        # the number of synapses in this subrow, then
        # scipy.stats.<dist>.ppf(p**K, **params) gives the (100*p)th percentile of
        # the maximum number of synapses in a subrow of this matrix
        K = float(N) / M

        # Each possible connection is made with probability p_connect
        return int(scipy.stats.binom.ppf(
            0.9999**K, N, self.p_connect))

    def _estimate_mean_row_synapses(self, pre_slice, post_slice,
                                    pre_size, post_size):
        return int(round(self.p_connect * float(len(post_slice))))

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

    def _estimate_mean_row_synapses(self, pre_slice, post_slice,
                                    pre_size, post_size):
        return 1 if pre_slice.overlaps(post_slice) else 0

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
    def _get_slice_row_length_histogram(self, pre_slice, post_slice):
        # Extract columns of pre and post indices from connection list
        pre_indices = self.conn_list[:, 0]
        post_indices = self.conn_list[:, 1]

        # Build mask to select list entries in slice
        mask = ((pre_indices >= pre_slice.start) &
                (pre_indices < pre_slice.stop) &
                (post_indices >= post_slice.start) &
                (post_indices < post_slice.stop))

        # Return histogram of masked pre-indices
        return np.bincount(pre_indices[mask].astype(int))

    def _estimate_max_row_synapses(self, pre_slice, post_slice,
                                   pre_size, post_size):
        # Get the row length histogram of slice
        hist = self._get_slice_row_length_histogram(pre_slice, post_slice)

        # Return maximum row length
        return np.amax(hist);

    def _estimate_mean_row_synapses(self, pre_slice, post_slice,
                                    pre_size, post_size):
        # Get the row length histogram of slice
        hist = self._get_slice_row_length_histogram(pre_slice, post_slice)

        # Return average row length
        return np.average(hist)

    def _get_projection_initial_state(self, pre_size, post_size):
        return None


# ----------------------------------------------------------------------------
# FixedNumberPostConnector
# ----------------------------------------------------------------------------
class FixedNumberPostConnector(FixedNumberPostConnector):
    # Can suitable populations connected with this connector be connected
    # using an in-memory buffer rather than by sending multicast packets
    _directly_connectable = False

    _on_chip_param_map = [("allow_self_connections", "u4", lazy_param_map.integer)]

    # --------------------------------------------------------------------------
    # Internal SpiNNaker methods
    # --------------------------------------------------------------------------
    def _estimate_max_row_synapses(self, pre_slice, post_slice,
                                   pre_size, post_size):
        # Each pre-synaptic neuron connects to n of the M=post_size
        # post-synaptic neurons.
        # Determining which of those n connections are within this post_slice is
        # a matter of sampling N=len(post_slice) times with or without replacement.
        # The number within the row and post_slice are
        # binomially or hypergeometrically distributed.

        N = len(post_slice)
        M = post_size

        # If scipy.stats.<dist>.ppf(p, **params) gives the (100*p)th percentile of
        # the number of synapses in this subrow, then
        # scipy.stats.<dist>.ppf(p**K, **params) gives the (100*p)th percentile of
        # the maximum number of synapses in a subrow of this matrix
        K = float(N) / (M * pre_size)

        if self.n == 0:
            return 0
        elif self.with_replacement:
            return int(scipy.stats.binom.ppf(0.9999**K, n=self.n, p=float(N)/M))
        else:
            return int(scipy.stats.hypergeom.ppf(0.9999**K, M=M, N=N, n=self.n)))

    def _estimate_mean_row_synapses(self, pre_slice, post_slice,
                                    pre_size, post_size):
        # How large a fraction of the full post populations is this
        post_fraction = float(len(post_slice)) / float(post_size)

        return int(self.n * post_fraction)

    def _get_projection_initial_state(self, pre_size, post_size):
        return None


# ----------------------------------------------------------------------------
# FixedNumberPreConnector
# ----------------------------------------------------------------------------
class FixedNumberPreConnector(FixedNumberPreConnector):
    # Can suitable populations connected with this connector be connected
    # using an in-memory buffer rather than by sending multicast packets
    _directly_connectable = False

    _on_chip_param_map = [("allow_self_connections", "u4", lazy_param_map.integer)]

    # --------------------------------------------------------------------------
    # Internal SpiNNaker methods
    # --------------------------------------------------------------------------
    def _estimate_max_row_synapses(self, pre_slice, post_slice,
                                   pre_size, post_size):
        # Each post-synaptic neuron connects to n of the M=pre_size
        # pre-synaptic neurons.

        N = len(post_slice)
        M = pre_size

        # If scipy.stats.<dist>.ppf(p, **params) gives the (100*p)th percentile of
        # the number of synapses in this subrow, then
        # scipy.stats.<dist>.ppf(p**K, **params) gives the (100*p)th percentile of
        # the maximum number of synapses in a subrow of this matrix
        K = float(N) / (M * pre_size)

        if self.n == 0:
            return 0
        elif self.with_replacement:
            # In the with replacement case, in each column, the number of connections
            # that end up in this row are distributed as Binom(n, 1/pre_size).
            # The number that end up in the sub-row are a sum of binomials, or
            # Binom(n*len(post_slice), 1/pre_size).
            return int(scipy.stats.binom.ppf(0.9999**K, n=self.n * N, p=1.0/pre_size))
        else:
            # In the without replacement case, the number of connections that end up
            # in a single column of this row is distributed as Bernoulli(n/pre_size).
            # The number that end up in this sub-row are distributed as
            # Binom(len(post_slice), n/pre_size).
            return int(scipy.stats.binom.ppf(0.9999**K, n=len(post_slice), p=self.n/float(pre_size))

        # Calculate the probability that any of the
        # n synapses in the column will be within this row
        prob_in_row = float(self.n) / pre_size

        # Return the row-length that 99.99% of rows will be shorter than
        return int(scipy.stats.binom.ppf(
            0.9999, len(post_slice), prob_in_row))

    def _estimate_mean_row_synapses(self, pre_slice, post_slice,
                                    pre_size, post_size):
        return int(len(post_slice) * float(self.n) / float(pre_size))

    def _get_projection_initial_state(self, pre_size, post_size):
        return None


# ----------------------------------------------------------------------------
# FixedTotalNumberConnector
# ----------------------------------------------------------------------------
class FixedTotalNumberConnector(FixedTotalNumberConnector):
    # Can suitable populations connected with this connector be connected
    # using an in-memory buffer rather than by sending multicast packets
    _directly_connectable = False

    _on_chip_param_map = [("allow_self_connections", "u4", lazy_param_map.integer),
                          ("with_replacement", "u4", lazy_param_map.integer),
                          (_draw_num_connections, "u4"),
                          (_submat_size, "u4")]

    # --------------------------------------------------------------------------
    # Internal SpiNNaker methods
    # --------------------------------------------------------------------------
    def _estimate_max_row_synapses(self, pre_slice, post_slice,
                                   pre_size, post_size):
        # There are n connections amongst the M=pre_size*post_size possible
        # connections.
        # Determining which of those n connections are within this row and
        # post_slice is a matter of sampling N=len(post_slice) times with
        # or without replacement. The number within the row and post_slice are
        # binomially or hypergeometrically distributed.

        M = pre_size * post_size
        N = len(post_slice)

        # If scipy.stats.<dist>.ppf(p, **params) gives the (100*p)th percentile of
        # the number of synapses in this subrow, then
        # scipy.stats.<dist>.ppf(p**K, **params) gives the (100*p)th percentile of
        # the maximum number of synapses in a subrow of this matrix
        K = float(N) / M

        if self.n == 0:
            return 0
        elif self.with_replacement:
            return int(scipy.stats.binom.ppf(0.9999**K, n=self.n, p=float(N)/M))
        else:
            return int(scipy.stats.hypergeom.ppf(0.9999**K, M=M, N=N, n=self.n))

    def _estimate_mean_row_synapses(self, pre_slice, post_slice,
                                    pre_size, post_size):
        # How large a fraction of the full post populations is this
        pre_fraction = float(len(pre_slice)) / float(pre_size)
        post_fraction = float(len(post_slice)) / float(post_size)

        # Multiply these by the total number of synapses
        return int(pre_fraction * post_fraction * float(self.n) / float(pre_size))

    def _get_projection_initial_state(self, pre_size, post_size):
        return {'n': self.n, 'N': pre_size * post_size,
                'with_replacement':self.with_replacement}
