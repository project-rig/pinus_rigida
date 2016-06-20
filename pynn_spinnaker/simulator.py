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
        self.machine_controller = None
        self.spalloc_job = None
        self.system_info = None
        self.dt = 0.1

        self.clear()

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

        # Mapping from post-synaptic PyNN population (i.e. the
        # one the current input cluster is injecting current INTO)
        # to list of current input clusters
        # {pynn_population: [current_input_cluster]}
        self.post_pop_current_input_clusters = defaultdict(list)

        # List of populations
        self.populations = []

        # List of projections
        self.projections = []

        # Stop any currently running SpiNNaker application
        self.stop()

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
            self.machine_controller = None

        # Destroy spalloc job if we have one
        if self.spalloc_job is not None:
            logger.info("Destroying spalloc job")
            self.spalloc_job.destroy()
            self.spalloc_job = None

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

            # Loop through synapse clusters
            for s_type, s_cluster in iteritems(pop._synapse_clusters):
                # If synapse cluster doesn't require back propagation, skip
                if not s_type.model._requires_back_propagation:
                    continue

                logger.debug("\t\tSynapse type:%s, receptor:%s",
                             s_type.model.__class__.__name__, s_type.receptor)

                # Loop through synapse vertices
                for s_vert in s_cluster.verts:
                    # Set synapse vetices list of back propagation
                    # input vertices to all neural cluster vertices
                    # whose neuron slices overlap
                    s_vert.back_prop_in_verts = [
                        n_vert for n_vert in pop._neural_cluster.verts
                        if s_vert.post_neuron_slice.overlaps(n_vert.neuron_slice)]

                    logger.debug("\t\t\tVertex %s has %u back propagation vertices",
                                 s_vert, len(s_vert.back_prop_in_verts))

        return constraints

    def _read_stats(self, duration_ms):
        logger.info("Reading stats")

        # Loop through populations
        duration_s = float(duration_ms) / 1000.0
        for pop in self.populations:
            for s_type, stats in iteritems(pop.get_synapse_statistics()):
                logger.info("\t\tSynapse type:%s receptor:%s",
                            s_type.model.__class__.__name__, s_type.receptor)
                logger.info("\t\t\tRows requested - Average per vertex per second:%f, Total per second:%f",
                            np.mean(stats["row_requested"]) / duration_s,
                            np.sum(stats["row_requested"]) / duration_s)
                logger.info("\t\t\tDelay rows requested - Average per vertex per second:%f, Total per second:%f",
                            np.mean(stats["delay_row_requested"]) / duration_s,
                            np.sum(stats["delay_row_requested"]) / duration_s)
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
        keyspace.add_field("pop_index", tags=("routing", "transmission"))
        keyspace.add_field("vert_index", tags=("routing", "transmission"))
        keyspace.add_field("flush", length=1, start_at=10, tags="transmission")
        keyspace.add_field("neuron_id", length=10, start_at=0)

        # Create empty dictionaries to contain Rig mappings
        # of vertices to  applications and resources
        vertex_applications = {}
        vertex_resources = {}

        # Allocate clusters
        # **NOTE** neuron clusters and hence vertices need to be allocated
        # first as synapse cluster allocateion is dependant on neuron vertices
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
        for proj in self.projections:
            # Create cluster
            c = proj._create_current_input_cluster(
                hardware_timestep_us, duration_timesteps,
                vertex_applications, vertex_resources)

            # Add cluster to data structures
            if c is not None:
                self.post_pop_current_input_clusters[proj.post].append(c)

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

        # If there isn't already a machine controller
        # **TODO** this probably doesn't belong here
        if self.machine_controller is None:
            logger.info("Connecting to SpiNNaker")

            # If we should use spalloc
            if self.spalloc_num_boards is not None:
                from spalloc import Job

                # Request the job
                self.spalloc_job = Job(self.spalloc_num_boards)
                logger.info("Allocated spalloc job ID %u",
                            self.spalloc_job.id)

                # Wait until we're given the machine
                logger.info("Waiting for spalloc machine allocation")
                self.spalloc_job.wait_until_ready()

                # spalloc recommends a slight delay before attempting to boot the
                # machine, later versions of spalloc server may relax this
                # requirement.
                time.sleep(5.0)

                # Store the hostname
                hostname = self.spalloc_job.hostname
                logger.info("Using %u board(s) of \"%s\" (%s)",
                            len(self.spalloc_job.boards),
                            self.spalloc_job.machine_name,
                            hostname)
            # Otherwise, use pre-configured hostname
            else:
                hostname = self.spinnaker_hostname

            # Get machine controller from connected SpiNNaker board and boot
            self.machine_controller = MachineController(hostname)
            self.machine_controller.boot()

            # Get system info
            self.system_info = self.machine_controller.get_system_info()
            logger.debug("Found %u chip machine", len(self.system_info))

        # Place-and-route
        logger.info("Placing and routing")
        placements, allocations, application_map, routing_tables =\
            place_and_route_wrapper(vertex_resources, vertex_applications,
                                    nets, net_keys, self.system_info, constraints)

        # Convert placement values to a set to get unique list of chips
        unique_chips = set(itervalues(placements))

        logger.info("Placed on %u cores (%u chips)",
                    len(placements), len(unique_chips))
        logger.debug(list(itervalues(placements)))

        # If software watchdog is disabled, write zero to each chip in
        # placement's SV struct, otherwise, write default from SV struct file
        wdog = (0 if self.disable_software_watchdog else
                self.machine_controller.structs["sv"]["soft_wdog"].default)
        for x, y in unique_chips:
            logger.debug("Setting software watchdog to %u for chip %u, %u",
                         wdog, x, y)
            self.machine_controller.write_struct_field("sv", "soft_wdog",
                                                       wdog, x, y)

        # Allocate buffers for SDRAM-based communication between vertices
        logger.info("Allocating population output buffers")
        for pop in self.populations:
            pop._allocate_out_buffers(placements, allocations,
                                      self.machine_controller)
        logger.info("Allocating projection output buffers")
        for proj in self.projections:
            proj._allocate_out_buffers(placements, allocations,
                                       self.machine_controller)

        # Load vertices
        # **NOTE** projection vertices need to be loaded
        # first as weight-fixed point is only calculated at
        # load time and this is required by neuron vertices
        logger.info("Loading projection vertices")
        for proj in self.projections:
            proj._load_verts(placements, allocations, self.machine_controller)

        logger.info("Loading population vertices")
        flush_mask = keyspace.get_mask(field="flush")
        for pop in self.populations:
            pop._load_verts(placements, allocations,
                            self.machine_controller, flush_mask)

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
