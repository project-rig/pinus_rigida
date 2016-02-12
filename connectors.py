"""
Connection method classes for pinus_rigida

:copyright: Copyright 2006-2015 by the PyNN team, see AUTHORS.
:license: CeCILL, see LICENSE for details.

"""
from pyNN.connectors import (AllToAllConnector,
                             FixedProbabilityConnector,
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

#------------------------------------------------------------------------------
# AllToAllConnector
#------------------------------------------------------------------------------
class AllToAllConnector(AllToAllConnector):
    directly_connectable = False

    def estimate_num_synapses(self, pre_slice, post_slice):
        return len(pre_slice) * len(post_slice)

#------------------------------------------------------------------------------
# FixedProbabilityConnector
#------------------------------------------------------------------------------
class FixedProbabilityConnector(FixedProbabilityConnector):
    directly_connectable = False

    def estimate_num_synapses(self, pre_slice, post_slice):
        return int(round(self.p_connect * float(len(pre_slice)) *
                         float(len(post_slice))))

#------------------------------------------------------------------------------
# OneToOneConnector
#------------------------------------------------------------------------------
class OneToOneConnector(OneToOneConnector):
    directly_connectable = True

    def estimate_num_synapses(self, pre_slice, post_slice):
        return min(len(pre_slice), len(post_slice))

#------------------------------------------------------------------------------
# FromListConnector
#------------------------------------------------------------------------------
class FromListConnector(FromListConnector):
    directly_connectable = False

    def estimate_num_synapses(self, pre_slice, post_slice):
        assert False, "The bloody list's already in memory - apply slices"
        return len(self.conn_list)