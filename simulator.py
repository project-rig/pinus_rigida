# Import modules
import itertools
import logging
import math
import os
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
# NeuronVertex
#------------------------------------------------------------------------------
class NeuronVertex(object):
    def __init__(self, parent_keyspace, neuron_slice, population_index, vertex_index):
        self.neuron_slice = neuron_slice
        self.keyspace = parent_keyspace(population_index=population_index, 
            vertex_index=vertex_index)
        self.input_verts = list()

    @property
    def key(self):
        return self.keyspace.get_value(tag="routing")
    
    @property
    def mask(self):
        return self.keyspace.get_mask(tag="routing")

    def __str__(self):
        return "<neuron slice:%s>" % (str(self.neuron_slice))

#------------------------------------------------------------------------------
# InputVertex
#------------------------------------------------------------------------------
class InputVertex(object):
    def __init__(self, post_neuron_slice, receptor_index):
        self.post_neuron_slice = post_neuron_slice
        self.weight_fixed_point = None
        self.receptor_index = receptor_index
        self.out_buffers = None

    def __str__(self):
        return "<post neuron slice:%s, receptor index:%u>" % (str(self.post_neuron_slice), self.receptor_index)

#------------------------------------------------------------------------------
# SynapseInputVertex
#------------------------------------------------------------------------------
class SynapseInputVertex(InputVertex):
    def __init__(self, post_neuron_slice, receptor_index):
        # Superclass
        super(SynapseInputVertex, self).__init__(post_neuron_slice, receptor_index)

        self.incoming_connections = defaultdict(list)

    def add_connection(self, pre_pop, pre_neuron_vertex):
        self.incoming_connections[pre_pop].append(pre_neuron_vertex)

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

        # Get directory of backend
        self.backend_dir = os.path.dirname(__file__)

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

    def _allocate_neuron_verts(self, vertex_applications, vertex_resources, keyspace):
        logger.info("Allocating neuron vertices")

        # Loop through populations whose output can't be
        # entirely be replaced by direct connections
        pop_neuron_verts = defaultdict(list)
        populations = [p for p in self.populations
                       if not p.entirely_directly_connectable]
        for pop_id, pop in enumerate(populations):
            logger.debug("\tPopulation:%s", pop.label)

            # Partition population to get slices and resources for each vertex
            # **TODO** check if population can be directly attached - for Poisson, rate, size fan-out calculation
            neuron_slices, neuron_resources = pop.partition()

            # Build neuron vertices for each slice allocating a keyspace for each vertex
            neuron_verts = [NeuronVertex(keyspace, neuron_slice, pop_id, vert_id)
                            for vert_id, neuron_slice in enumerate(neuron_slices)]

            # Add resultant list of vertices to dictionary
            pop_neuron_verts[pop] = neuron_verts

            # Get neuron application name
            # **THINK** is there any point in doing anything cleverer than this
            neuron_app = os.path.join(
                self.backend_dir, "model_binaries",
                "neuron_" + pop.celltype.__class__.__name__.lower() + ".aplx")

            logger.debug("\t\tNeuron application:%s" % neuron_app)
            logger.debug("\t\t%u neuron vertices" % len(neuron_verts))

            # Loop through neuron vertices and their corresponding resources
            for v, r in zip(neuron_verts, neuron_resources):
                # Add application to dictionary
                vertex_applications[v] = neuron_app

                # Add resources to dictionary
                vertex_resources[v] = r

        return pop_neuron_verts

    def _allocate_synapse_verts(self, vertex_applications, vertex_resources):
        logger.info("Allocating synapse vertices")

        # Now all neuron vertices are partioned,
        # loop through populations again
        # **TODO** make this process iterative so if result of
        # there are more than 15 synapse processors for each
        # neuron processor, split more and try again
        # **TODO** post-synaptic limits should perhaps be based on
        # shifts down of 1024 to avoid overlapping weirdness
        pop_synapse_verts = defaultdict(lambda: defaultdict(list))
        for pop in self.populations:
            logger.debug("\tPopulation:%s", pop.label)

            # Loop through newly partioned incoming projections
            for synapse_type, pre_pop_projections in iteritems(pop.incoming_projections):
                # Chain together incoming projections from all populations
                projections = list(itertools.chain.from_iterable(itervalues(pre_pop_projections)))
                synaptic_projections = [p for p in projections
                                        if not p.directly_connectable]

                # Slice post-synaptic neurons evenly based on synapse type
                post_slices = evenly_slice(
                    pop.size, synapse_type[0].max_post_neurons_per_core)

                receptor_index = pop.celltype.receptor_types.index(synapse_type[1])
                logger.debug("\t\tSynapse type:%s, Receptor index:%u"
                    % (synapse_type, receptor_index))

                # Get synapse application name
                # **THINK** is there any point in doing anything cleverer than this
                synapse_app = os.path.join(
                    self.backend_dir, "model_binaries",
                    "synapse_" + synapse_type[0].__name__.lower() + ".aplx")
                logger.debug("\t\t\tSynapse application:%s" % synapse_app)

                # Loop through the post-slices
                synapse_verts = []
                for post_slice in post_slices:
                    logger.debug("\t\t\tPost slice:%s" % str(post_slice))

                    # Loop through all non-directly connectable projections of this type
                    synapse_vertex_event_rate = 0.0
                    synapse_vertex = SynapseInputVertex(post_slice, receptor_index)
                    for projection in synaptic_projections:
                        # **TODO** nengo-style configuration system
                        mean_pre_firing_rate = 10.0

                        # **TODO** check if projection and pre-population can be directly attached
                        # Loop through the vertices which the pre-synaptic
                        # population has been partitioned into
                        for pre_vertex in self.pop_neuron_verts[projection.pre]:
                            logger.debug("\t\t\t\tPre slice:%s", str(pre_vertex.neuron_slice))

                            # Estimate number of synapses the connection between
                            # The pre and the post-slice of neurons will contain
                            total_synapses = projection.estimate_num_synapses(
                                pre_vertex.neuron_slice, post_slice)

                            # Use this to calculate event rate
                            synaptic_event_rate = total_synapses * mean_pre_firing_rate

                            # **TODO** SDRAM estimation
                            logger.debug("\t\t\t\t\tTotal synapses:%d, synaptic event rate:%f" % (total_synapses, synaptic_event_rate))

                            # Add this connection to the synapse vertex
                            synapse_vertex.add_connection(projection.pre, pre_vertex)

                            # Add event rate to total for current synapse processor
                            synapse_vertex_event_rate += synaptic_event_rate

                            # If it's more than this type of synapse processor can handle
                            if synapse_vertex_event_rate > synapse_type[0].max_synaptic_event_rate:
                                # Add current synapse vertex to list
                                synapse_verts.append(synapse_vertex)

                                # Create replacement and reset event rate
                                synapse_vertex = SynapseInputVertex(post_slice, receptor_index)
                                synapse_vertex_event_rate = 0.0

                    # If the last synapse vertex created had any incoming connections
                    if len(synapse_vertex.incoming_connections) > 0:
                        synapse_verts.append(synapse_vertex)

                logger.debug("\t\t\t%u synapse vertices" % len(synapse_verts))

                # Loop through synapse vertices
                for v in synapse_verts:
                    # Add application to dictionary
                    vertex_applications[v] = synapse_app

                    # Add resources to dictionary
                    # **TODO** add SDRAM
                    vertex_resources[v] = { machine.Cores: 1 }

                # Add synapse vertices to dictionary
                if len(synapse_verts) > 0:
                    pop_synapse_verts[pop][synapse_type] = synapse_verts

        return pop_synapse_verts

    def _allocate_current_input_verts(self, vertex_applications, vertex_resources):
        logger.info("Allocating current input vertices")
        proj_current_input_verts = defaultdict(list)
        post_pop_current_input_verts = defaultdict(list)
        for pop in self.populations:
            logger.debug("\tPopulation:%s" % pop.label)

            # Chain together the lists of incoming projections
            # From all synapse types and pre-synaptic populations
            projections = itertools.chain.from_iterable(
                itertools.chain.from_iterable(itervalues(p))
                for p in itervalues(pop.incoming_projections))

            # Loop through those that are directly connectable
            current_input_verts = []
            for proj in (p for p in projections if p.directly_connectable):
                logger.debug("\t\tProjection:%s" % proj.label)

                # Slice current input
                post_slices = evenly_slice(
                    proj.pre.size,
                    proj.pre.celltype.max_current_inputs_per_core)

                # Get receptor index this projection should connect to
                receptor_index = proj.post.celltype.receptor_types.index(proj.receptor_type)

                # Get current input application name
                # **THINK** is there any point in doing anything cleverer than this
                current_input_app = os.path.join(
                    self.backend_dir, "model_binaries",
                    "current_input_" + proj.pre.celltype.__class__.__name__.lower() + ".aplx")
                logger.debug("\t\t\tCurrent input application:%s"
                    % current_input_app)

                # Loop through slices
                for post_slice in post_slices:
                    logger.debug("\t\t\tPost slice:%s" % str(post_slice))

                    # Build input vert and add to list
                    input_vert = InputVertex(post_slice, receptor_index)
                    current_input_verts.append(input_vert)

                    # Add application to dictionary
                    vertex_applications[input_vert] = current_input_app

                    # Add resources to dictionary
                    # **TODO** add SDRAM
                    vertex_resources[input_vert] = { machine.Cores: 1 }

                logger.debug("\t\t\t%u current input vertices" % len(current_input_verts))

                # Assign list of vertices to post-synaptic population's
                # list of current input vertices and to projection
                if len(current_input_verts) > 0:
                    post_pop_current_input_verts[proj.post].extend(current_input_verts)
                    proj_current_input_verts[proj].extend(current_input_verts)

        return proj_current_input_verts, post_pop_current_input_verts

    def _build_nets(self):
        logger.info("Building nets")

        # Loop through all projections in simulation
        nets = []
        net_keys = {}
        for pop, n_verts in iteritems(self.pop_neuron_verts):
            # If population has any outgoing connections
            if len(pop.outgoing_projections) > 0:
                logger.debug("\tPopulation label:%s" % pop.label)

                # Get synapse verts associated with post-synaptic population
                post_s_verts = list(itertools.chain.from_iterable(
                    [self.pop_synapse_verts[o.post][o.spinnaker_synapse_type]
                    for o in pop.outgoing_projections]))

                logger.debug("\t\t%u post-synaptic vertices" %
                             len(post_s_verts))

                # Loop through each neuron vertex that makes up population
                for n_vert in n_verts:
                    # Create a key for this source neuron vertex
                    net_key = (n_vert.key, n_vert.mask)

                    # Create a net connecting neuron vertex to synapse vertices
                    net = Net(n_vert, post_s_verts)

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
            # Get lists of synapse and neuron vertices
            # associated with this PyNN population
            s_verts = list(itertools.chain.from_iterable(
                itervalues(self.pop_synapse_verts[pop])))
            c_verts = self.post_pop_current_input_verts[pop]
            n_verts = self.pop_neuron_verts[pop]

            # If there are any synapse vertices
            if len(s_verts) > 0 or len(c_verts) > 0:
                logger.debug("\tPopulation:%s", pop.label)

                # Loop through neuron vertices
                for n in n_verts:
                    # Find synapse and current vertices with the same slice
                    # **TODO** different ratios here
                    n.input_verts = [i for i in itertools.chain(s_verts, c_verts)
                                       if i.post_neuron_slice == n.neuron_slice]

                    logger.debug("\t\tConstraining neuron vert %s and input verts %s to same chip" % (n, n.input_verts))

                    # Build same chip constraint and add to list
                    constraints.append(SameChipConstraint(n.input_verts + [n]))

        return constraints

    def _load_synapse_verts(self, placements, allocations,
                            hardware_timestep_us, duration_timesteps):
        logger.info("Loading synapse vertices")

        # Build synapse populations
        spinnaker_synapse_pops = {}
        for pop, synapse_types in iteritems(self.pop_synapse_verts):
            # Loop through synapse types and associated vertices
            for s_type, s_verts in iteritems(synapse_types):
                logger.debug("\tPopulation label:%s, synapse type:%s" %
                            (pop.label, str(s_type)))

                # If this population has any synapse vertices of this type
                if len(s_verts) > 0:
                    # Expand any incoming connections
                    matrices, weight_fixed_point = pop.build_incoming_connection(s_type)

                    # Create a spinnaker population
                    spinnaker_pop = pop.create_spinnaker_synapse_population(
                        weight_fixed_point, hardware_timestep_us,
                        duration_timesteps)

                    # Add spinnaker population to dictionary
                    spinnaker_synapse_pops[pop] = spinnaker_pop

                    # Loop through synapse verts
                    for v in s_verts:
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
                            spinnaker_pop.partition_matrices(matrices,
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
                            size = spinnaker_pop.get_size(
                                v.post_neuron_slice, sub_matrices,
                                matrix_placements, v.out_buffers)

                            # Allocate a suitable memory block
                            # for this vertex and get memory io
                            # **NOTE** this is tagged by core
                            memory_io = self.machine_controller.sdram_alloc_as_filelike(
                                size, tag=core.start)
                            logger.debug("\t\t\tMemory with tag:%u begins at:%08x"
                                        % (core.start, memory_io.address))

                            # Write the vertex to file
                            spinnaker_pop.write_to_file(
                                v.post_neuron_slice, sub_matrices,
                                matrix_placements, v.out_buffers, memory_io)

        return spinnaker_synapse_pops

    def _load_current_input_verts(self, placements, allocations,
                                  hardware_timestep_us, duration_timesteps):
        logger.info("Loading current input vertices")

        # Build current input populations
        spinnaker_current_input_pops = defaultdict(list)
        for proj, c_verts in iteritems(self.proj_current_input_verts):
            logger.debug("\tProjection label:%s from population label:%s" %
                         (proj.label, proj.pre.label))

            # Build direct connection for projection
            direct_weights = proj.build_direct_connection()

            # Create a spinnaker population
            spinnaker_pop = proj.pre.create_spinnaker_current_input_population(
                self.dt, hardware_timestep_us, duration_timesteps, direct_weights)

            # Add spinnaker population to dictionary
            spinnaker_current_input_pops[proj.pre].append(spinnaker_pop)

            # Loop through synapse verts
            for v in c_verts:
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
                    size = spinnaker_pop.get_size(
                        v.post_neuron_slice, v.out_buffers)

                    # Allocate a suitable memory block
                    # for this vertex and get memory io
                    # **NOTE** this is tagged by core
                    memory_io = self.machine_controller.sdram_alloc_as_filelike(
                        size, tag=core.start)
                    logger.debug("\t\t\tMemory with tag:%u begins at:%08x"
                                    % (core.start, memory_io.address))

                    # Write the vertex to file
                    spinnaker_pop.write_to_file(
                        v.post_neuron_slice, v.out_buffers, memory_io)

        return spinnaker_current_input_pops

    def _load_neuron_verts(self, placements, allocations,
                           hardware_timestep_us, duration_timesteps):
        logger.info("Loading neuron vertices")

        # Build neural populations
        spinnaker_neuron_pops = {}
        for pop, verts in iteritems(self.pop_neuron_verts):
            logger.debug("\tPopulation label:%s" % pop.label)

            # Create spinnaker neural population
            spinnaker_pop = pop.create_spinnaker_neural_population(
                self.dt, hardware_timestep_us,
                duration_timesteps)

            # Add spinnaker population to dictionary
            spinnaker_neuron_pops[pop] = spinnaker_pop

            # Loop through vertices
            for v in verts:
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
                    size = spinnaker_pop.get_size(
                        v.key, v.neuron_slice, in_buffers)

                    # Allocate a suitable memory block
                    # for this vertex and get memory io
                    # **NOTE** this is tagged by core
                    memory_io = self.machine_controller.sdram_alloc_as_filelike(
                        size, tag=core.start)
                    logger.debug("\t\t\tMemory with tag:%u begins at:%08x"
                                 % (core.start, memory_io.address))

                    # Write the vertex to file
                    v.region_memory = spinnaker_pop.write_to_file(
                        v.key, v.neuron_slice, in_buffers, memory_io)

        return spinnaker_neuron_pops

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

        # Allocate vertices
        self.pop_neuron_verts =\
            self._allocate_neuron_verts(vertex_applications, vertex_resources,
                                        keyspace)
        self.pop_synapse_verts =\
            self._allocate_synapse_verts(vertex_applications, vertex_resources)
        self.proj_current_input_verts, self.post_pop_current_input_verts =\
            self._allocate_current_input_verts(vertex_applications,
                                               vertex_resources)

        # Constrain clusters of vertices to same chip
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

        # Load vertices
        self.spinnaker_synapse_pops = self._load_synapse_verts(
            placements, allocations, hardware_timestep_us, duration_timesteps)

        # Load vertices
        self.spinnaker_current_input_pops = self._load_current_input_verts(
            placements, allocations, hardware_timestep_us, duration_timesteps)

        self.spinnaker_neuron_pops = self._load_neuron_verts(
            placements, allocations, hardware_timestep_us, duration_timesteps)


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
