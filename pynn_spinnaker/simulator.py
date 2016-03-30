# Import modules
import itertools
import logging
import math
import numpy as np
import time
from rig import machine

# Import classes
from collections import defaultdict
from pyNN import common
from rig.bitfield import BitField
from rig.machine_control.consts import AppState, signal_types, AppSignal, MessageType
from rig.machine_control.machine_controller import MachineController
from rig.place_and_route.constraints import SameChipConstraint

# Import functions
from rig.place_and_route import place_and_route_wrapper
from six import iteritems, itervalues

logger = logging.getLogger("pynn_spinnaker")

name = "SpiNNaker"


# ----------------------------------------------------------------------------
# ID
# ----------------------------------------------------------------------------
class ID(int, common.IDMixin):
    def __init__(self, n):
        """Create an ID object with numerical value `n`."""
        int.__init__(n)
        common.IDMixin.__init__(self)


# ----------------------------------------------------------------------------
# State
# ----------------------------------------------------------------------------
class State(common.control.BaseState):
    # These are required to be present for various
    # bits of PyNN, but not really relevant for SpiNNaker
    mpi_rank = 0
    num_processes = 1

    def __init__(self):
        common.control.BaseState.__init__(self)
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

    def stop(self):
        if self.machine_controller is not None and self.stop_on_spinnaker:
            logger.info("Stopping SpiNNaker application")
            self.machine_controller.send_signal("stop")

    def _wait_for_transition(self, placements, allocations,
                             from_state, to_state,
                             num_verts):
        while True:
            # If no cores are still in from_state, stop
            if self.machine_controller.count_cores_in_state(from_state) == 0:
                break

            # Wait a bit
            time.sleep(1.0)

        # Wait for all cores to reach to_state
        cores_in_to_state =\
            self.machine_controller.wait_for_cores_to_reach_state(
                to_state, num_verts, timeout=5.0)
        if cores_in_to_state != num_verts:
            # Loop through all placed vertices
            for vertex, (x, y) in iteritems(placements):
                p = allocations[vertex][machine.Cores].start
                status = self.machine_controller.get_processor_status(p, x, y)
                if status.cpu_state is not to_state:
                    print("Core ({}, {}, {}) in state {!s}".format(
                        x, y, p, status))
                    print self.machine_controller.get_iobuf(p, x, y)
            raise Exception("Unexpected core failures "
                            "before reaching %s state (%u/%u)." % (to_state, cores_in_to_state, num_verts))

    def _estimate_constraints(self, hardware_timestep_us):
        logger.info("Estimating constraints")

        # Loop through populations whose output can't be
        # entirely be replaced by direct connections
        populations = [p for p in self.populations
                       if not p._entirely_directly_connectable]
        for pop_id, pop in enumerate(populations):
            logger.debug("\tPopulation:%s", pop.label)
            pop._estimate_constraints(hardware_timestep_us)

    def _allocate_current_input_clusters(self, vertex_applications,
                                         vertex_resources,
                                         hardware_timestep_us,
                                         duration_timesteps):
        logger.info("Allocating current input clusters")

        # Mapping from PyNN projection to current input cluster
        # {pynn_projection: current_input_cluster}
        proj_current_input_clusters = {}

        # Mapping from post-synaptic PyNN population (i.e. the
        # one the current input cluster is injecting current INTO)
        # to list of current input clusters
        # {pynn_population: [current_input_cluster]}
        post_pop_current_input_clusters = defaultdict(list)

        # Loop through projections
        for proj in self.projections:
            # If this projection isn't directory connectable
            if not proj._directly_connectable:
                continue

            logger.debug("\t\tProjection:%s", proj.label)

            # Create cluster
            c = proj._create_current_input_cluster(
                hardware_timestep_us, duration_timesteps,
                vertex_applications, vertex_resources)

            # Add cluster to data structures
            post_pop_current_input_clusters[proj.post].append(c)
            proj_current_input_clusters[proj] = c

        return proj_current_input_clusters, post_pop_current_input_clusters

    def _constrain_clusters(self):
        logger.info("Constraining vertex clusters to same chip")

        # Loop through populations
        constraints = []
        for pop in self.populations:
            # If population has no neuron cluster, skip
            if pop._neural_cluster is None:
                continue

            # Get lists of synapse, neuron and current input
            # vertices associated with this PyNN population
            s_verts = list(itertools.chain.from_iterable(
                c.verts for c in itervalues(pop._synapse_clusters)))
            c_verts = list(itertools.chain.from_iterable(
                c.verts for c in self.post_pop_current_input_clusters[pop]))

            # If there are any synapse vertices
            if len(s_verts) > 0 or len(c_verts) > 0:
                logger.debug("\tPopulation:%s", pop.label)

                # Loop through neuron vertices
                for n in pop._neural_cluster.verts:
                    # Find synapse and current vertices
                    # with overlapping slices
                    n.input_verts = [
                        i for i in itertools.chain(s_verts, c_verts)
                        if i.post_neuron_slice.overlaps(n.neuron_slice)]

                    logger.debug("\t\tConstraining neuron vert and %u input "
                                 "verts to same chip", len(n.input_verts))

                    # Build same chip constraint and add to list
                    constraints.append(SameChipConstraint(n.input_verts + [n]))

        return constraints

    def _load_synapse_verts(self, placements, allocations,
                            hardware_timestep_us, duration_timesteps):
        logger.info("Loading synapse vertices")

        # Loop through populations
        for pop in self.populations:
            # Loop through synapse types and associated cluster
            for s_type, s_cluster in iteritems(pop._synapse_clusters):
                logger.info("\tPopulation label:%s, synapse type:%s, receptor:%s",
                            pop.label, s_type.model.__class__.__name__,
                            s_type.receptor)

                # Expand any incoming connections
                matrices, weight_fixed_point =\
                    pop._build_incoming_connection(s_type)

                # Loop through synapse verts
                for v in s_cluster.verts:
                    # Cache weight fixed-point for
                    # this synapse point in vertex
                    v.weight_fixed_point = weight_fixed_point

                    # Get placement and allocation
                    vertex_placement = placements[v]
                    vertex_allocation = allocations[v]

                    # Get core this vertex should be run on
                    core = vertex_allocation[machine.Cores]
                    assert (core.stop - core.start) == 1

                    logger.debug("\t\tVertex %s (%u, %u, %u)",
                             v, vertex_placement[0], vertex_placement[1],
                             core.start)

                    # Partition the matrices
                    sub_matrices, matrix_placements =\
                        s_cluster.partition_matrices(matrices,
                                                     v.post_neuron_slice,
                                                     v.incoming_connections)

                    # Select placed chip
                    with self.machine_controller(x=vertex_placement[0],
                                                 y=vertex_placement[1]):
                        # Allocate two output buffers
                        # for this synapse population
                        out_buffer_bytes = len(v.post_neuron_slice) * 4
                        v.out_buffers = [
                            self.machine_controller.sdram_alloc(
                                out_buffer_bytes, clear=True)
                            for _ in range(2)]

                        # Calculate required memory size
                        size, allocs = s_cluster.get_size(
                            v.post_neuron_slice, sub_matrices,
                            matrix_placements, weight_fixed_point,
                            v.out_buffers)

                        # Allocate a suitable memory block
                        # for this vertex and get memory io
                        # **NOTE** this is tagged by core
                        memory_io =\
                            self.machine_controller.sdram_alloc_as_filelike(
                                size, tag=core.start)
                        logger.debug("\t\t\tMemory with tag:%u begins at:%08x",
                                     core.start, memory_io.address)

                        # Write the vertex to file
                        v.region_memory = s_cluster.write_to_file(
                            v.post_neuron_slice, sub_matrices,
                            matrix_placements, weight_fixed_point,
                            v.out_buffers, memory_io)

    def _load_current_input_verts(self, placements, allocations,
                                  hardware_timestep_us, duration_timesteps):
        logger.info("Loading current input vertices")

        # Build current input populations
        for proj, c_cluster in iteritems(self.proj_current_input_clusters):
            logger.info("\tProjection label:%s from population label:%s",
                         proj.label, proj.pre.label)

            # Build direct connection for projection
            direct_weights = proj._build_direct_connection()

            # Loop through synapse verts
            for v in c_cluster.verts:
                # Use native S16.15 format
                v.weight_fixed_point = 15

                # Get placement and allocation
                vertex_placement = placements[v]
                vertex_allocation = allocations[v]

                # Get core this vertex should be run on
                core = vertex_allocation[machine.Cores]
                assert (core.stop - core.start) == 1

                logger.debug("\t\tVertex %s (%u, %u, %u)",
                             v, vertex_placement[0], vertex_placement[1],
                             core.start)

                # Select placed chip
                with self.machine_controller(x=vertex_placement[0],
                                             y=vertex_placement[1]):
                    # Allocate two output buffers for this synapse population
                    out_buffer_bytes = len(v.post_neuron_slice) * 4
                    v.out_buffers = [
                        self.machine_controller.sdram_alloc(
                            out_buffer_bytes, clear=True)
                        for _ in range(2)]

                    # Calculate required memory size
                    size, allocs = c_cluster.get_size(v.post_neuron_slice,
                                                      direct_weights,
                                                      v.out_buffers)

                    # Allocate a suitable memory block
                    # for this vertex and get memory io
                    # **NOTE** this is tagged by core
                    memory_io =\
                        self.machine_controller.sdram_alloc_as_filelike(
                            size, tag=core.start)
                    logger.debug("\t\t\tMemory with tag:%u begins at:%08x",
                                 core.start, memory_io.address)

                    # Write the vertex to file
                    v.region_memory = c_cluster.write_to_file(
                        v.post_neuron_slice, direct_weights, v.out_buffers,
                        memory_io)

    def _load_neuron_verts(self, placements, allocations,
                           hardware_timestep_us, duration_timesteps):
        logger.info("Loading neuron vertices")

        # Build neural populations
        for pop in self.populations:
            # If population has no neuron cluster, skip
            if pop._neural_cluster is None:
                continue

            logger.info("\tPopulation label:%s", pop.label)

            # Loop through vertices
            for v in pop._neural_cluster.verts:
                # Get placement and allocation
                vertex_placement = placements[v]
                vertex_allocation = allocations[v]

                # Get core this vertex should be run on
                core = vertex_allocation[machine.Cores]
                assert (core.stop - core.start) == 1

                logger.debug("\t\tVertex %s (%u, %u, %u): Key:%08x",
                             v, vertex_placement[0], vertex_placement[1],
                             core.start, v.key)

                # Select placed chip
                with self.machine_controller(x=vertex_placement[0],
                                             y=vertex_placement[1]):
                    # Get the input buffers from each synapse vertex
                    in_buffers = [
                        (s.get_in_buffer(v.neuron_slice), s.receptor_index,
                         s.weight_fixed_point)
                        for s in v.input_verts]

                    # Calculate required memory size
                    size, allocs = pop._neural_cluster.get_size(v.key,
                                                                v.neuron_slice,
                                                                in_buffers)

                    # Allocate a suitable memory block
                    # for this vertex and get memory io
                    # **NOTE** this is tagged by core
                    memory_io =\
                        self.machine_controller.sdram_alloc_as_filelike(
                            size, tag=core.start)
                    logger.debug("\t\t\tMemory with tag:%u begins at:%08x",
                                 core.start, memory_io.address)

                    # Write the vertex to file
                    v.region_memory = pop._neural_cluster.write_to_file(
                        v.key, v.neuron_slice, in_buffers, memory_io)

    def _read_stats(self, duration_ms):
        logger.info("Reading stats")

        # Loop through populations
        duration_s = float(duration_ms) / 1000.0
        for pop in self.populations:
            for s_type, stats in iteritems(pop.get_synapse_statistics()):
                logger.info("\t\tSynapse type:%s receptor:%s",
                            s_type.model.__class__.__name__, s_type.receptor)
                logger.info("\t\t\tRows requested per vertex per second:%f",
                            np.mean(stats["row_requested"]) / duration_s)
                logger.info("\t\t\tDelay rows requested per vertex per second:%f",
                            np.mean(stats["delay_row_requested"]) / duration_s)
                logger.info("\t\t\tDelay buffers not processed:%u",
                            np.sum(stats["delay_buffers_not_processed"]))
                logger.info("\t\t\tInput buffer overflows:%u",
                            np.sum(stats["input_buffer_overflows"]))
                logger.info("\t\t\tKey lookup failures:%u",
                            np.sum(stats["key_lookup_fails"]))


    def _build(self, duration_ms):
        # Convert dt into microseconds and divide by
        # realtime proportion to get hardware timestep
        hardware_timestep_us = int(round((1000.0 * float(self.dt)) /
                                         float(self.realtime_proportion)))

        # Determine how long simulation is in timesteps
        duration_timesteps =\
            int(math.ceil(float(duration_ms) / float(self.dt)))

        logger.info("Simulating for %u %fms timesteps "
                    "using a hardware timestep of %uus",
                    duration_timesteps, self.dt, hardware_timestep_us)

        # Estimate constraints
        self._estimate_constraints(hardware_timestep_us)

        # Create a 32-bit keyspace
        keyspace = BitField(32)
        keyspace.add_field("population_index", tags="routing")
        keyspace.add_field("vertex_index", tags="routing")
        keyspace.add_field("neuron_id", length=10, start_at=0,
                           tags="application")

        # Create empty dictionaries to contain Rig mappings
        # of vertices to  applications and resources
        vertex_applications = {}
        vertex_resources = {}

        # Allocate clusters
        logger.info("Allocating neuron clusters")
        for pop_id, pop in enumerate(self.populations):
            logger.debug("\tPopulation:%s", pop.label)
            pop._create_neural_cluster(pop_id, hardware_timestep_us, duration_timesteps,
                                       vertex_applications, vertex_resources, keyspace)

        logger.info("Allocating synapse clusters")
        for pop in self.populations:
            logger.debug("\tPopulation:%s", pop.label)
            pop._create_synapse_clusters(hardware_timestep_us, duration_timesteps,
                                       vertex_applications, vertex_resources)

        logger.info("Allocating current input clusters")
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
        logger.info("Building nets")

        # Loop through all populations and build nets
        nets = []
        net_keys = {}
        for pop in self.populations:
            pop._build_nets(nets, net_keys)

        logger.info("Connecting to SpiNNaker")

        # Get machine controller from connected SpiNNaker board and boot
        self.machine_controller = MachineController(self.spinnaker_hostname)
        self.machine_controller.boot()

        # Get system info
        system_info = self.machine_controller.get_system_info()
        logger.debug("Found %u chip machine", len(system_info))

        # Place-and-route
        logger.info("Placing and routing")
        placements, allocations, application_map, routing_tables =\
            place_and_route_wrapper(vertex_resources, vertex_applications,
                                    nets, net_keys, system_info, constraints)
        logger.info("Placed on %u cores", len(placements))
        logger.debug(list(itervalues(placements)))

        # If software watchdog is disabled, write zero to each chip in
        # placement's SV struct, otherwise, write default from SV struct file
        wdog = (0 if self.disable_software_watchdog else
                self.machine_controller.structs["sv"]["soft_wdog"].default)
        for x, y in set(itervalues(placements)):
            logger.debug("Setting software watchdog to %u for chip %u, %u",
                         wdog, x, y)
            self.machine_controller.write_struct_field("sv", "soft_wdog",
                                                       wdog, x, y)

        # Load vertices
        self._load_synapse_verts(placements, allocations,
                                 hardware_timestep_us, duration_timesteps)

        self._load_current_input_verts(placements, allocations,
                                       hardware_timestep_us,
                                       duration_timesteps)

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

        self._read_stats(duration_ms)
state = State()
