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
from rig.place_and_route.constraints import SameChipConstraint
from rig.netlist import Net

# Import functions
from rig.place_and_route import wrapper
from six import iteritems
from spinnaker.utils import evenly_slice

logger = logging.getLogger("pinus_rigida")

name = "SpiNNaker"

def generate_nets_and_keys(pre_pop, post, pop_neuron_vertices,
                           pop_synapse_vertices):
    # Loop through vertices that contain
    # The neurons of the pre-synaptic population
    nets = []
    net_keys = []
    for pre_vert in pop_neuron_vertices[pre_pop]:
        # Add key to list
        net_keys.append((pre_vert.key, pre_vert.mask))
        
        # If post-synaptic population is an assembly
        if isinstance(post, common.Assembly):
            # Add the vertices that contain each post-synaptic
            # population in the assembly's synapses to list
            sink_vertices = []
            for post_pop in post.populations:
                sinks.extend(pop_synapse_vertices[post_pop])
            nets.append(Net(pre_vert, sink_vertices))

        # Otherwise, just add a single net connecting pre-vertex to all
        # vertices contain the post-synaptic population's synapses
        # **TODO** population views
        else:
            nets.append(Net(pre_vert, pop_synapse_vertices[post]))

    return nets, net_keys

#------------------------------------------------------------------------------
# NeuronVertex
#------------------------------------------------------------------------------
class NeuronVertex:
    def __init__(self, parent_keyspace, neuron_slice, population_index, vertex_index):
        self.neuron_slice = neuron_slice
        self.keyspace = parent_keyspace(population_index=population_index, 
            vertex_index=vertex_index)
        self.synapse_verts = None

    @property
    def key(self):
        return self.keyspace.get_value(tag="routing")
    
    @property
    def mask(self):
        return self.keyspace.get_mask(tag="routing")

#------------------------------------------------------------------------------
# SynapseVertex
#------------------------------------------------------------------------------
class SynapseVertex:
    def __init__(self, post_neuron_slice, receptor_index):
        self.post_neuron_slice = post_neuron_slice
        self.incoming_connections = defaultdict(list)
        self.receptor_index = receptor_index
        self.out_buffers = None

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

    def run(self, simtime):
        # Build data
        self._build(simtime)
        
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
                             num_vertices):
        while True:
            # If no cores are still in from_state, stop
            if self.machine_controller.count_cores_in_state(from_state) == 0:
                break

            # Wait a bit
            time.sleep(1.0)

        # Check if any cores haven't exited cleanly
        if self.machine_controller.count_cores_in_state(desired_to_state) != num_vertices:
            # Loop through all SpiNNaker populations
            for pop, vertices in itertools.chain(
                iteritems(self.pop_neuron_vertices),
                iteritems(self.pop_synapse_vertices)):

                # Loop through their vertices
                for v in vertices:
                    x, y = placements[v]
                    p = allocations[v][machine.Cores].start
                    status = self.machine_controller.get_processor_status(p, x, y)
                    if status.cpu_state is not desired_to_state:
                        print("Core ({}, {}, {}) in state {!s}".format(
                            x, y, p, status.cpu_state))
                        print self.machine_controller.get_iobuf(p, x, y)
            raise Exception("Unexpected core failures before reaching %s state." % desired_to_state)

    def _build(self, duration_ms):
        # Convert timestep to microseconds
        simulation_timestep_us = int(round(1000.0 * self.dt))
        
        # Divide by realtime proportion to get hardware timestep 
        hardware_timestep_us = int(round(float(simulation_timestep_us) /
                                         float(self.realtime_proportion)))
        
        # Determine how long simulation is in timesteps
        duration_timesteps = int(round(float(duration_ms) / float(self.dt)))
        
        logger.info("Simulating for %u %uus timesteps using a hardware timestep of %uus" %
            (duration_timesteps, simulation_timestep_us, hardware_timestep_us))
        
        # Create a 32-bit keyspace
        keyspace = BitField(32)
        keyspace.add_field("population_index", tags="routing")
        keyspace.add_field("vertex_index", tags="routing")
        keyspace.add_field("neuron_id", length=10, start_at=0, tags="application")
        
        # Get directory of backend
        backend_dir = os.path.dirname(__file__)
        
        logger.info("Partitioning neuron vertices")

        # Loop through populations
        self.pop_neuron_vertices = {}
        vertex_applications = {}
        vertex_resources = {}
        for pop_id, pop in enumerate(self.populations):
            logger.debug("Population:%s", pop.label)

            # Partition population to get slices and resources for each vertex
            neuron_slices, neuron_resources = pop.partition()
            
            # Build neuron vertices for each slice allocating a keyspace for each vertex
            neuron_vertices = [NeuronVertex(keyspace, neuron_slice, pop_id, vert_id)
                               for vert_id, neuron_slice in enumerate(neuron_slices)]
            
            # Add resultant list of vertices to dictionary
            self.pop_neuron_vertices[pop] = neuron_vertices
            
            # Get neuron application name
            # **THINK** is there any point in doing anything cleverer than this
            neuron_application = os.path.join(
                backend_dir, "model_binaries",
                "neuron_processor_" + pop.celltype.__class__.__name__.lower() + ".aplx")

            logger.debug("\tNeuron application:%s" % neuron_application)
            
            # Loop through neuron vertices and their corresponding resources
            for v, r in zip(neuron_vertices, neuron_resources):
                # Add application to dictionary
                vertex_applications[v] = neuron_application

                # Add resources to dictionary
                vertex_resources[v] = r

        logger.info("Partitioning synapse vertices")

        # Now all neuron vertices are partioned,
        # loop through populations again
        # **TODO** make this process iterative so if result of
        # there are more than 15 synapse processors for each
        # neuron processor, split more and try again
        # **TODO** post-synaptic limits should perhaps be based on
        # shifts down of 1024 to avoid overlapping weirdness
        self.pop_synapse_vertices = {}
        for pop in self.populations:
            logger.debug("Population:%s", pop.label)

            # Partition incoming projections to this population by type
            pop_synapse_types = defaultdict(list)
            for pre_pop, projections in iteritems(pop.incoming_projections):
                for p in projections:
                    # Build a tuple identifying which synapse
                    # type this projection requires
                    synapse_type = (p.synapse_type.__class__, p.receptor_type)

                    # Add this population to the associated list
                    pop_synapse_types[synapse_type].append(p)

            # Loop through newly partioned incoming projections
            synapse_vertices = []
            for synapse_type, projections in iteritems(pop_synapse_types):
                # Slice post-synaptic neurons evenly based on synapse type
                post_slices = evenly_slice(
                    pop.size, synapse_type[0].max_post_neurons_per_core)

                receptor_index = pop.celltype.receptor_types.index(synapse_type[1])
                logger.debug("\tSynapse type:%s, Receptor type:%s(%u)" % (synapse_type[0].__name__, synapse_type[1], receptor_index))

                # Get synapse application name
                # **THINK** is there any point in doing anything cleverer than this
                synapse_application = os.path.join(
                    backend_dir, "model_binaries",
                    "synapse_processor_" + synapse_type[0].__name__.lower() + ".aplx")
                logger.debug("\t\tSynapse application:%s" % synapse_application)

                # Loop through the post-slices
                for post_slice in post_slices:
                    logger.debug("\t\tPost slice:", post_slice)
                    
                    # Loop through all projections of this type
                    synapse_vertex_event_rate = 0.0
                    synapse_vertex = SynapseVertex(post_slice, receptor_index)
                    for projection in projections:
                        # **TODO** nengo-style configuration system
                        mean_pre_firing_rate = 10.0

                        # Loop through the vertices which the pre-synaptic
                        # population has been partitioned into
                        for pre_vertex in self.pop_neuron_vertices[projection.pre]:
                            logger.debug("\t\t\t\tPre slice:", pre_vertex.neuron_slice)

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
                                synapse_vertices.append(synapse_vertex)

                                # Create replacement and reset event rate
                                synapse_vertex = SynapseVertex(post_slice, receptor_index)
                                synapse_vertex_event_rate = 0.0

                    # If the last synapse vertex created had any incoming connections
                    if len(synapse_vertex.incoming_connections) > 0:
                        synapse_vertices.append(synapse_vertex)
                    logger.debug("\t\t\t%u synapse vertices" % len(synapse_vertices))

            logger.debug("\t\t%u synapse vertices" % len(synapse_vertices))

            # Add synapse vertices to dictionary
            self.pop_synapse_vertices[pop] = synapse_vertices

            # Loop through synapse vertices
            for v in synapse_vertices:
                # Add application to dictionary
                vertex_applications[v] = synapse_application

                # Add resources to dictionary
                vertex_resources[v] = { machine.Cores: 1 }

        logger.info("Constraining synapse and neuron vertices together")

        # Loop through population again to constrain
        # together synapse and neuron vertices
        constraints = []
        for pop in self.populations:
            logger.debug("\tPopulation:", pop)

            # Get lists of synapse and neuron vertices associated with this list
            s_verts = self.pop_synapse_vertices[pop]
            n_verts = self.pop_neuron_vertices[pop]

            # Loop through neuron vertices
            num_assoc_s_verts = 0
            for n in n_verts:
                # Find synapse vertices with the same slice
                # **TODO** different ratios here
                n.synapse_verts = [s for s in s_verts
                                   if s.post_neuron_slice == n.neuron_slice]

                # Count associated neuron vertices
                num_assoc_s_verts += len(n.synapse_verts)

                logger.debug("\t\tConstraining neuron vert %s and synapse verts %s to same chip" % (n, n.synapse_verts))

                # Build same chip constraint and add to list
                constraints.append(SameChipConstraint(n.synapse_verts + [n]))

        # Finalise keyspace fields
        keyspace.assign_fields()

        # Loop through all projections in simulation
        nets = []
        net_keys = {}
        for proj in self.projections:
            # If pre-synaptic side of projection connects to an aseembly, 
            # Generate a net for each population in the assembly
            if isinstance(proj.pre, common.Assembly):
                 for pre_pop in proj.pre.populations:
                    # Generate list of nets and their key coming from this population
                    vertex_nets, vertex_net_keys = generate_nets_and_keys(
                        pre_pop, proj.post,
                        self.pop_neuron_vertices, self.pop_synapse_vertices)
                    
                    # Add to global lists
                    nets.extend(vertex_nets)
                    net_keys.update(zip(vertex_nets, vertex_net_keys))
            # Otherwise, it's a single population
            # **TODO** population view
            else:
                # Generate list of nets and their key coming from this population
                vertex_nets, vertex_net_keys = generate_nets_and_keys(
                    proj.pre, proj.post,
                    self.pop_neuron_vertices, self.pop_synapse_vertices)
                
                # Add to global lists
                nets.extend(vertex_nets)
                net_keys.update(zip(vertex_nets, vertex_net_keys))
            
        logger.info("Connecting to SpiNNaker")

        # Get machine controller from connected SpiNNaker board
        self.machine_controller = MachineController(self.spinnaker_hostname)
        # **TODO** some sensible/ideally standard with Nengo booting behaviour
        self.machine_controller.boot(2, 2)

        # Retrieve a machine object
        spinnaker_machine = self.machine_controller.get_machine()

        logger.debug("Found %ux%u chip machine" %
            (spinnaker_machine.width, spinnaker_machine.height))

        logger.info("Placing and routing")

        # Place-and-route
        placements, allocations, application_map, routing_tables = wrapper(
            vertex_resources, vertex_applications, nets, net_keys,
            spinnaker_machine, constraints)
        
        logger.info("Writing synapse vertices")

        # Build synapse populations
        self.spinnaker_synapse_pops = {}
        for pop, vertices in iteritems(self.pop_synapse_vertices):
            logger.debug("\tPopulation %s" % pop)

            # Expand any incoming connections
            matrices, incoming_weight_range = pop.build_incoming_connection()

            # Create a spinnaker population
            spinnaker_pop = pop.create_spinnaker_synapse_population(
                incoming_weight_range, hardware_timestep_us,
                duration_timesteps)

            # Add spinnaker population to dictionary
            self.spinnaker_synapse_pops[pop] = spinnaker_pop

            # Loop through vertices
            for v in vertices:
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
                    logger.debug("\tMemory begins at %08x" % memory_io.address)

                    # Write the vertex to file
                    spinnaker_pop.write_to_file(
                        v.post_neuron_slice, sub_matrices,
                        matrix_placements, v.out_buffers, memory_io)
        
        logger.info("Writing neuron vertices")
        
        # Build neural populations
        self.spinnaker_neuron_pops = {}
        for pop, vertices in iteritems(self.pop_neuron_vertices):
            logger.debug("\tPopulation %s" % pop.label)

            # Create spinnaker neural population
            spinnaker_pop = pop.create_spinnaker_neural_population(
                simulation_timestep_us, hardware_timestep_us,
                duration_timesteps)

            # Add spinnaker population to dictionary
            self.spinnaker_neuron_pops[pop] = spinnaker_pop

            # Loop through vertices
            for v in vertices:
                logger.debug("\t\tVertex slice %s" % str(v.neuron_slice))

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
                    in_buffers = [(s.out_buffers, s.receptor_index)
                                  for s in v.synapse_verts]

                    # Calculate required memory size
                    size = spinnaker_pop.get_size(
                        v.key, v.neuron_slice,in_buffers)

                    # Allocate a suitable memory block
                    # for this vertex and get memory io
                    # **NOTE** this is tagged by core
                    memory_io = self.machine_controller.sdram_alloc_as_filelike(
                        size, tag=core.start)
                    logger.debug("\tMemory begins at %08x" % memory_io.address)

                    # Write the vertex to file
                    spinnaker_pop.write_to_file(v.key, v.neuron_slice,
                                                in_buffers, memory_io)

        # Load routing tables and applications
        logger.info("Loading routing tables")
        self.machine_controller.load_routing_tables(routing_tables)
        logger.info("Loading applications")
        self.machine_controller.load_application(application_map)

        # Wait for all cores to hit SYNC0
        logger.info("Waiting for synch")
        num_vertices = len(vertex_resources)
        self._wait_for_transition(placements, allocations,
                                  AppState.init, AppState.sync0,
                                  num_vertices)

        # Sync!
        self.machine_controller.send_signal("sync0")

        # Wait for simulation to complete
        logger.info("Simulating")
        time.sleep(float(duration_ms) / 1000.0)

        # Wait for all cores to exit
        logger.info("Waiting for exit")
        self._wait_for_transition(placements, allocations,
                                  AppState.run, AppState.exit,
                                  num_vertices)
state = State()
