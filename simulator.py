# Import modules
import itertools
import logging
import math
import time
from rig import machine

# Import classes
from collections import defaultdict
from pyNN import common
from rig.bitfield import BitField
from rig.machine_control.consts import AppState
from rig.machine_control.machine_controller import MachineController, MemoryIO
from rig.place_and_route.constraints import (ReserveResourceConstraint,
                                             SameChipConstraint)
from rig.netlist import Net

# Import functions
from rig.place_and_route import wrapper
from six import iteritems, itervalues
from spinnaker.utils import evenly_slice

logger = logging.getLogger("pinus_rigida")

name = "SpiNNaker"

#------------------------------------------------------------------------------
# ID
#------------------------------------------------------------------------------
class ID(int, common.IDMixin):
    def __init__(self, n):
        """Create an ID object with numerical value `n`."""
        int.__init__(n)
        common.IDMixin.__init__(self)

#------------------------------------------------------------------------------
# State
#------------------------------------------------------------------------------
class State(common.control.BaseState):
    def __init__(self):
        common.control.BaseState.__init__(self)
        self.mpi_rank = 0
        self.num_processes = 1
        self.clear()
        self.dt = 0.1
        self.populations = []
        self.projections = []

    def run(self, simtime):
        # Build data
        try:
            self._build(simtime)
        except:
            self.end()
        
        self.t += simtime
        self.running = True
        
    def run_until(self, tstop):
        # Build data
        self._build(tstop - self.t)
        
        self.t = tstop
        self.running = True
        
    def clear(self):
        self.recorders = set([])
        self.id_counter = 42
        self.segment_counter = -1
        self.reset()
        
    def reset(self):
        """Reset the state of the current network to time t = 0."""
        self.running = False
        self.t = 0
        self.t_start = 0
        self.segment_counter += 1

    def end(self):
        if self.machine_controller is not None:
            logger.info("Stopping SpiNNaker application")
            self.machine_controller.send_signal("stop")

    def _wait_for_transition(self, placements, allocations,
                             from_state, desired_to_state,
                             num_verts):
        while True:
            # If no cores are still in from_state, stop
            if self.machine_controller.count_cores_in_state(from_state) == 0:
                break

            # Wait a bit
            time.sleep(1.0)

        # Check if any cores haven't exited cleanly
        if self.machine_controller.count_cores_in_state(desired_to_state) != num_verts:
            # Loop through all placed vertices
            for vertex, (x,y) in iteritems(placements):
                p = allocations[vertex][machine.Cores].start
                status = self.machine_controller.get_processor_status(p, x, y)
                if status.cpu_state is not desired_to_state:
                    print("Core ({}, {}, {}) in state {!s}".format(
                        x, y, p, status.cpu_state))
                    print self.machine_controller.get_iobuf(p, x, y)
            raise Exception("Unexpected core failures before reaching %s state." % desired_to_state)

    def _allocate_neuron_clusters(self, vertex_applications, vertex_resources,
                                  keyspace, hardware_timestep_us,
                                  duration_timesteps):
        logger.info("Allocating neuron clusters")

        # Loop through populations whose output can't be
        # entirely be replaced by direct connections
        pop_neuron_clusters = {}
        populations = [p for p in self.populations
                       if not p.entirely_directly_connectable]
        for pop_id, pop in enumerate(populations):
            logger.debug("\tPopulation:%s", pop.label)

            # Create spinnaker neural cluster
            pop_neuron_clusters[pop] = pop.create_neural_cluster(
                pop_id, self.dt, hardware_timestep_us, duration_timesteps,
                vertex_applications, vertex_resources, keyspace)

        return pop_neuron_clusters

    def _allocate_synapse_clusters(self, vertex_applications, vertex_resources,
                                   hardware_timestep_us, duration_timesteps):
        logger.info("Allocating synapse clusters")

        # Now all neuron vertices are partioned,
        # loop through populations again
        # **TODO** make this process iterative so if result of
        # there are more than 15 synapse processors for each
        # neuron processor, split more and try again
        # **TODO** post-synaptic limits should perhaps be based on
        # shifts down of 1024 to avoid overlapping weirdness
        pop_synapse_clusters = {}
        for pop in self.populations:
            logger.debug("\tPopulation:%s", pop.label)

            # Create neural clusters for this population
            pop_synapse_clusters[pop] = pop.create_synapse_clusters(
                hardware_timestep_us, duration_timesteps,
                vertex_applications, vertex_resources)

        return pop_synapse_clusters

    def _allocate_current_input_clusters(self, vertex_applications,
                                         vertex_resources, hardware_timestep_us,
                                         duration_timesteps):
        logger.info("Allocating current input clusters")

        proj_current_input_clusters = {}
        post_pop_current_input_clusters = defaultdict(list)
        for proj in self.projections:
            if not proj.directly_connectable:
                continue

            logger.debug("\t\tProjection:%s" % proj.label)

            # Create cluster
            c = proj.create_current_input_cluster(
                self.dt, hardware_timestep_us, duration_timesteps,
                vertex_applications, vertex_resources)

            # Add cluster to data structures
            post_pop_current_input_clusters[proj.post].append(c)
            proj_current_input_clusters[proj] = c

        return proj_current_input_clusters, post_pop_current_input_clusters

    def _build_nets(self):
        logger.info("Building nets")

        # Loop through all neuron clusters
        nets = []
        net_keys = {}
        for pop, n_cluster in iteritems(self.pop_neuron_clusters):
            # If population has outgoing projections and neuron vertices
            if len(pop.outgoing_projections) > 0 and len(n_cluster.verts) > 0:
                logger.debug("\tPopulation label:%s" % pop.label)

                # Get synapse vertices associated with post-synaptic population
                post_s_verts = list(itertools.chain.from_iterable(
                    [self.pop_synapse_clusters[o.post][o.synapse_cluster_type].verts
                    for o in pop.outgoing_projections]))

                logger.debug("\t\t%u post-synaptic vertices" %
                             len(post_s_verts))

                # Loop through each neuron vertex that makes up population
                for n_vert in n_cluster.verts:
                    # Get subset of the synapse vertices that need
                    # to be connected to this neuron vertex
                    filtered_post_s_verts = [s for s in post_s_verts
                                             if n_vert in s.incoming_connections[pop]]

                    # Create a key for this source neuron vertex
                    net_key = (n_vert.key, n_vert.mask)

                    # Create a net connecting neuron vertex to synapse vertices
                    net = Net(n_vert, filtered_post_s_verts)

                    # Add net to list and associate with key
                    nets.append(net)
                    net_keys[net] = net_key

        return nets, net_keys

    def _constrain_clusters(self):
        logger.info("Constraining vertex clusters to same chip")

        # Loop through population again to constrain
        # together synapse and neuron vertices
        constraints = []
        for pop in self.populations:
            # If population has no neuron cluster, skip
            if pop not in self.pop_neuron_clusters:
                continue

            # Get lists of synapse and neuron vertices
            # associated with this PyNN population
            s_verts = list(itertools.chain.from_iterable(
                [c.verts for c in itervalues(self.pop_synapse_clusters[pop])]))
            c_verts = list(itertools.chain.from_iterable(
                [c.verts for c in self.post_pop_current_input_clusters[pop]]))
            n_verts = self.pop_neuron_clusters[pop].verts

            # If there are any synapse vertices
            if len(s_verts) > 0 or len(c_verts) > 0:
                logger.debug("\tPopulation:%s", pop.label)

                # Loop through neuron vertices
                for n in n_verts:
                    # Find synapse and current vertices with the same slice
                    # **TODO** different ratios here
                    n.input_verts = [i for i in itertools.chain(s_verts, c_verts)
                                       if i.post_neuron_slice == n.neuron_slice]

                    logger.debug("\t\tConstraining neuron vert and %u input verts to same chip" % len(n.input_verts))

                    # Build same chip constraint and add to list
                    constraints.append(SameChipConstraint(n.input_verts + [n]))

        return constraints

    def _load_synapse_verts(self, placements, allocations,
                            hardware_timestep_us, duration_timesteps):
        logger.info("Loading synapse vertices")

        # Loop through populations
        for pop, synapse_types in iteritems(self.pop_synapse_clusters):
            # Loop through synapse types and associated cluster
            for s_type, s_cluster in iteritems(synapse_types):
                logger.debug("\tPopulation label:%s, synapse type:%s" %
                            (pop.label, str(s_type)))

                # If this cluster has any vertices
                if len(s_cluster.verts) > 0:
                    # Expand any incoming connections
                    matrices, weight_fixed_point = pop.build_incoming_connection(s_type)

                    # Loop through synapse verts
                    for v in s_cluster.verts:
                        logger.debug("\t\tVertex %s" % v)

                        # Cache weight fixed-point for this synapse point in vertex
                        v.weight_fixed_point = weight_fixed_point

                        # Get placement and allocation
                        vertex_placement = placements[v]
                        vertex_allocation = allocations[v]

                        # Get core this vertex should be run on
                        core = vertex_allocation[machine.Cores]
                        assert (core.stop - core.start) == 1

                        # Partition the matrices
                        sub_matrices, matrix_placements =\
                            s_cluster.partition_matrices(matrices,
                                                         v.post_neuron_slice,
                                                         v.incoming_connections)

                        # Select placed chip
                        with self.machine_controller(x=vertex_placement[0],
                                                    y=vertex_placement[1]):
                            # Allocate two output buffers for this synapse population
                            out_buffer_bytes = v.post_neuron_slice.slice_length * 4
                            v.out_buffers = [
                                self.machine_controller.sdram_alloc(
                                    out_buffer_bytes, clear=True)
                                for b in range(2)]

                            # Calculate required memory size
                            size = s_cluster.get_size(
                                v.post_neuron_slice, sub_matrices,
                                matrix_placements, weight_fixed_point,
                                v.out_buffers)

                            # Allocate a suitable memory block
                            # for this vertex and get memory io
                            # **NOTE** this is tagged by core
                            memory_io = self.machine_controller.sdram_alloc_as_filelike(
                                size, tag=core.start)
                            logger.debug("\t\t\tMemory with tag:%u begins at:%08x"
                                        % (core.start, memory_io.address))

                            # Write the vertex to file
                            s_cluster.write_to_file(
                                v.post_neuron_slice, sub_matrices,
                                matrix_placements, weight_fixed_point,
                                v.out_buffers, memory_io)

    def _load_current_input_verts(self, placements, allocations,
                                  hardware_timestep_us, duration_timesteps):
        logger.info("Loading current input vertices")

        # Build current input populations
        for proj, c_cluster in iteritems(self.proj_current_input_clusters):
            logger.debug("\tProjection label:%s from population label:%s" %
                         (proj.label, proj.pre.label))

            # Build direct connection for projection
            direct_weights = proj.build_direct_connection()

            # Loop through synapse verts
            for v in c_cluster.verts:
                logger.debug("\t\tVertex %s" % v)

                # Use native S15.16 format
                v.weight_fixed_point = 16

                # Get placement and allocation
                vertex_placement = placements[v]
                vertex_allocation = allocations[v]

                # Get core this vertex should be run on
                core = vertex_allocation[machine.Cores]
                assert (core.stop - core.start) == 1

                # Select placed chip
                with self.machine_controller(x=vertex_placement[0],
                                             y=vertex_placement[1]):
                    # Allocate two output buffers for this synapse population
                    out_buffer_bytes = v.post_neuron_slice.slice_length * 4
                    v.out_buffers = [
                        self.machine_controller.sdram_alloc(
                            out_buffer_bytes, clear=True)
                        for b in range(2)]

                    # Calculate required memory size
                    size = c_cluster.get_size(v.post_neuron_slice,
                                              direct_weights, v.out_buffers)

                    # Allocate a suitable memory block
                    # for this vertex and get memory io
                    # **NOTE** this is tagged by core
                    memory_io = self.machine_controller.sdram_alloc_as_filelike(
                        size, tag=core.start)
                    logger.debug("\t\t\tMemory with tag:%u begins at:%08x"
                                    % (core.start, memory_io.address))

                    # Write the vertex to file
                    c_cluster.write_to_file(v.post_neuron_slice,
                                            direct_weights, v.out_buffers,
                                            memory_io)

    def _load_neuron_verts(self, placements, allocations,
                           hardware_timestep_us, duration_timesteps):
        logger.info("Loading neuron vertices")

        # Build neural populations
        for pop, n_cluster in iteritems(self.pop_neuron_clusters):
            logger.debug("\tPopulation label:%s" % pop.label)

            # Loop through vertices
            for v in n_cluster.verts:
                logger.debug("\t\tVertex %s" % v)

                # Get placement and allocation
                vertex_placement = placements[v]
                vertex_allocation = allocations[v]

                # Get core this vertex should be run on
                core = vertex_allocation[machine.Cores]
                assert (core.stop - core.start) == 1

                # Select placed chip
                with self.machine_controller(x=vertex_placement[0],
                                             y=vertex_placement[1]):
                    # Get the input buffers from each synapse vertex
                    in_buffers = [
                        (s.out_buffers, s.receptor_index, s.weight_fixed_point)
                        for s in v.input_verts]

                    # Calculate required memory size
                    size = n_cluster.get_size(v.key, v.neuron_slice,
                                              in_buffers)

                    # Allocate a suitable memory block
                    # for this vertex and get memory io
                    # **NOTE** this is tagged by core
                    memory_io = self.machine_controller.sdram_alloc_as_filelike(
                        size, tag=core.start)
                    logger.debug("\t\t\tMemory with tag:%u begins at:%08x"
                                 % (core.start, memory_io.address))

                    # Write the vertex to file
                    v.region_memory = n_cluster.write_to_file(
                        v.key, v.neuron_slice, in_buffers, memory_io)

    def _build(self, duration_ms):
        # Convert dt into microseconds and divide by
        # realtime proportion to get hardware timestep
        hardware_timestep_us = int(round((1000.0 * float(self.dt)) /
                                         float(self.realtime_proportion)))
        
        # Determine how long simulation is in timesteps
        duration_timesteps = int(math.ceil(float(duration_ms) / float(self.dt)))

        logger.info("Simulating for %u %ums timesteps using a hardware timestep of %uus" %
            (duration_timesteps, self.dt, hardware_timestep_us))
        
        # Create a 32-bit keyspace
        keyspace = BitField(32)
        keyspace.add_field("population_index", tags="routing")
        keyspace.add_field("vertex_index", tags="routing")
        keyspace.add_field("neuron_id", length=10, start_at=0, tags="application")
        
        # Create empty dictionaries to contain Rig mappings
        # of vertices to  applications and resources
        vertex_applications = {}
        vertex_resources = {}

        # Allocate clusters
        self.pop_neuron_clusters = self._allocate_neuron_clusters(
            vertex_applications, vertex_resources, keyspace,
            hardware_timestep_us, duration_timesteps)

        self.pop_synapse_clusters = self._allocate_synapse_clusters(
            vertex_applications, vertex_resources,
            hardware_timestep_us, duration_timesteps)

        self.proj_current_input_clusters, self.post_pop_current_input_clusters =\
            self._allocate_current_input_clusters(
                vertex_applications, vertex_resources, hardware_timestep_us,
                duration_timesteps)

        # Constrain all vertices in clusters to same chip
        constraints = self._constrain_clusters()

        logger.info("Assigning keyspaces")

        # Finalise keyspace fields
        keyspace.assign_fields()

        # Build nets
        nets, net_keys = self._build_nets()

        logger.info("Connecting to SpiNNaker")

        # Get machine controller from connected SpiNNaker board and boot
        self.machine_controller = MachineController(self.spinnaker_hostname)
        self.machine_controller.boot(self.spinnaker_width, self.spinnaker_height)

        # Retrieve a machine object
        spinnaker_machine = self.machine_controller.get_machine()

        logger.debug("Found %ux%u chip machine" %
            (spinnaker_machine.width, spinnaker_machine.height))

        # If we should reserve extra cores on each chip e.g. for network tester
        # **TODO** integrate new Rig API to make this unnecessary
        if self.reserve_extra_cores_per_chip > 0:
            logger.info("Reserving %u extra cores per-chip"
                        % self.reserve_extra_cores_per_chip)

            # Reserve these extra cores (above monitor) on each chip
            reservation = slice(1, 1 + self.reserve_extra_cores_per_chip)
            constraints.append(ReserveResourceConstraint(machine.Cores,
                                                         reservation))

        logger.info("Placing and routing")

        # Place-and-route
        placements, allocations, application_map, routing_tables = wrapper(
            vertex_resources, vertex_applications, nets, net_keys,
            spinnaker_machine, constraints)
        logger.debug("Placing on %u cores", len(placements))
        logger.debug(list(itervalues(placements)))

        # Load vertices
        self._load_synapse_verts(placements, allocations,
                                 hardware_timestep_us, duration_timesteps)

        self._load_current_input_verts(placements, allocations,
                                       hardware_timestep_us, duration_timesteps)

        self._load_neuron_verts(placements, allocations, hardware_timestep_us,
                                duration_timesteps)


        # Load routing tables and applications
        logger.info("Loading routing tables")
        self.machine_controller.load_routing_tables(routing_tables)
        logger.info("Loading applications")
        self.machine_controller.load_application(application_map)

        # Wait for all cores to hit SYNC0
        logger.info("Waiting for synch")
        num_verts = len(vertex_resources)
        self._wait_for_transition(placements, allocations,
                                  AppState.init, AppState.sync0,
                                  num_verts)

        # Sync!
        self.machine_controller.send_signal("sync0")

        # Wait for simulation to complete
        logger.info("Simulating")
        time.sleep(float(duration_ms) / 1000.0)

        # Wait for all cores to exit
        logger.info("Waiting for exit")
        self._wait_for_transition(placements, allocations,
                                  AppState.run, AppState.exit,
                                  num_verts)
state = State()
