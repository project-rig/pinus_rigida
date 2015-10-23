# Import modules
import itertools
import math
import os
from rig import machine

# Import classes
from collections import defaultdict
from pyNN import common
from rig.bitfield import BitField
from rig.machine_control.machine_controller import MachineController, MemoryIO
from rig.netlist import Net

# Import functions
from rig.place_and_route import wrapper
from six import iteritems
from spinnaker.utils import evenly_slice

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
    def __init__(self, post_neuron_slice):
        self.post_neuron_slice = post_neuron_slice
        self.incoming_connections = []

    def add_connection(self, pre_neuron_vertex, projection):
        self.incoming_connections.append((pre_neuron_vertex, projection))

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
    
    def _build(self, duration_ms):
        # Convert timestep to microseconds
        simulation_timestep_us = int(round(1000.0 * self.dt))
        
        # Divide by realtime proportion to get hardware timestep 
        hardware_timestep_us = int(round(float(simulation_timestep_us) /
                                         float(self.realtime_proportion)))
        
        # Determine how long simulation is in timesteps
        duration_timesteps = int(round(float(duration_ms) / float(self.dt)))
        
        print("Simulating for %u %uus timesteps using a hardware timestep of %uus" % 
            (duration_timesteps, simulation_timestep_us, hardware_timestep_us))
        
        # Create a 32-bit keyspace
        keyspace = BitField(32)
        keyspace.add_field("population_index", tags="routing")
        keyspace.add_field("vertex_index", tags="routing")
        keyspace.add_field("neuron_id", length=10, start_at=0, tags="application")
        
        # Get directory of backend
        backend_dir = os.path.dirname(__file__)
        
        print("Partitioning neuron vertices")

        # Loop through populations
        pop_neuron_vertices = {}
        vertex_applications = {}
        vertex_resources = {}
        for pop_id, pop in enumerate(self.populations):
            print "Population:", pop

            # Partition population to get slices and resources for each vertex
            neuron_slices, neuron_resources = pop.partition()
            
            # Build neuron vertices for each slice allocating a keyspace for each vertex
            neuron_vertices = [NeuronVertex(keyspace, neuron_slice, pop_id, vert_id)
                               for vert_id, neuron_slice in enumerate(neuron_slices)]
            
            # Add resultant list of vertices to dictionary
            pop_neuron_vertices[pop] = neuron_vertices
            
            # Get neuron application name
            # **THINK** is there any point in doing anything cleverer than this
            neuron_application = os.path.join(
                backend_dir, "model_binaries",
                "neuron_processor_" + pop.celltype.__class__.__name__.lower() + ".aplx")

            print("\tNeuron application:%s" % neuron_application)
            
            # Loop through neuron vertices and their corresponding resources
            for v, r in zip(neuron_vertices, neuron_resources):
                # Add application to dictionary
                vertex_applications[v] = neuron_application

                # Add resources to dictionary
                vertex_resources[v] = r

        print("Partitioning synapse vertices")

        # Now all neuron vertices are partioned,
        # loop through populations again
        # **TODO** make this process iterative so if result of
        # there are more than 15 synapse processors for each
        # neuron processor, split more and try again
        # **TODO** post-synaptic limits should perhaps be based on
        # shifts down of 1024 to avoid overlapping weirdness
        pop_synapse_vertices = {}
        for pop in self.populations:
            print "Population:", pop

            # Partition incoming projections to this population by type
            pop_synapse_types = defaultdict(list)
            for p in pop.incoming_projections:
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

                print "\tSynapse type:", synapse_type[0].__name__, synapse_type[1]

                # Get synapse application name
                # **THINK** is there any point in doing anything cleverer than this
                synapse_application = os.path.join(
                    backend_dir, "model_binaries",
                    "synapse_processor_" + synapse_type[0].__name__.lower() + ".aplx")
                print("\t\tSynapse application:%s" % synapse_application)

                # Loop through the post-slices
                for post_slice in post_slices:
                    print "\t\tPost slice:", post_slice

                    # Loop through all projections of this type
                    synapse_vertex_event_rate = 0.0
                    synapse_vertex = SynapseVertex(post_slice)
                    for projection in projections:
                        print "\t\t\tProjection:", projection

                        # **TODO** nengo-style configuration system
                        mean_pre_firing_rate = 10.0

                        # Loop through the vertices which the pre-synaptic
                        # population has been partitioned into
                        for pre_vertex in pop_neuron_vertices[projection.pre]:
                            print "\t\t\t\tPre slice:", pre_vertex.neuron_slice

                            # Estimate number of synapses the connection between
                            # The pre and the post-slice of neurons will contain
                            total_synapses = projection.estimate_num_synapses(
                                pre_vertex.neuron_slice, post_slice)

                            # Use this to calculate event rate
                            synaptic_event_rate = total_synapses * mean_pre_firing_rate

                            # **TODO** SDRAM estimation
                            print "\t\t\t\t\tTotal synapses:%d, synaptic event rate:%f" % (total_synapses, synaptic_event_rate)

                            # Add this connection to the synapse vertex
                            synapse_vertex.add_connection(pre_vertex, projection)

                            # Add event rate to total for current synapse processor
                            synapse_vertex_event_rate += synaptic_event_rate

                            # If it's more than this type of synapse processor can handle
                            if synapse_vertex_event_rate > synapse_type[0].max_synaptic_event_rate:
                                # Add current synapse vertex to list
                                synapse_vertices.append(synapse_vertex)

                                # Create replacement and reset event rate
                                synapse_vertex = SynapseVertex(post_slice)
                                synapse_vertex_event_rate = 0.0

                    # If the last synapse vertex created had any incoming connections
                    if len(synapse_vertex.incoming_connections) > 0:
                        synapse_vertices.append(synapse_vertex)
                    print "\t\t\t%u synapse vertices" % len(synapse_vertices)

            print "\t\t%u synapse vertices" % len(synapse_vertices)

            # Add synapse vertices to dictionary
            pop_synapse_vertices[pop] = synapse_vertices

            # Loop through synapse vertices
            for v in synapse_vertices:
                # Add application to dictionary
                vertex_applications[v] = synapse_application

                # Add resources to dictionary
                vertex_resources[v] = { machine.Cores: 1 }

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
                        pop_neuron_vertices, pop_synapse_vertices)
                    
                    # Add to global lists
                    nets.extend(vertex_nets)
                    net_keys.update(zip(vertex_nets, vertex_net_keys))
            # Otherwise, it's a single population
            # **TODO** population view
            else:
                # Generate list of nets and their key coming from this population
                vertex_nets, vertex_net_keys = generate_nets_and_keys(
                    proj.pre, proj.post,
                    pop_neuron_vertices, pop_synapse_vertices)
                
                # Add to global lists
                nets.extend(vertex_nets)
                net_keys.update(zip(vertex_nets, vertex_net_keys))
            
        print("Connecting to SpiNNaker")

        # Get machine controller from connected SpiNNaker board
        machine_controller = MachineController(self.spinnaker_hostname)
        # **TODO** some sensible/ideally standard with Nengo booting behaviour
        machine_controller.boot(2, 2)

        # Retrieve a machine object
        spinnaker_machine = machine_controller.get_machine()

        print("Found %ux%u chip machine" %
            (spinnaker_machine.width, spinnaker_machine.height))

        print("Placing and routing")

        # Place-and-route
        placements, allocations, application_map, routing_tables = wrapper(
            vertex_resources, vertex_applications, nets, net_keys, spinnaker_machine)

        #print placements, allocations, application_map, routing_tables
        print("Writing vertices")
        
        # Build neural populations
        for pop, vertices in iteritems(pop_neuron_vertices):
            # Create spinnaker neural population
            spinnaker_pop = pop.create_spinnaker_neural_population(
                simulation_timestep_us, hardware_timestep_us,
                duration_timesteps)

            # Loop through vertices
            for v in vertices:
                # Get placement and allocation
                vertex_placement = placements[v]
                vertex_allocation = allocations[v]

                # Get core this vertex should be run on
                core = vertex_allocation[machine.Cores]
                assert (core.stop - core.start) == 1

                # Select placed chip
                with machine_controller(x=vertex_placement[0], y=vertex_placement[1]):
                    # Allocate a suitable memory block for this vertex and get memory io
                    # **NOTE** this is tagged by core
                    memory_io = machine_controller.sdram_alloc_as_filelike(
                        spinnaker_pop.get_size(v.key, v.neuron_slice), tag=core.start)
                    print("\tMemory begins at %08x" % memory_io.address)

                    # Write the vertex to file
                    spinnaker_pop.write_to_file(v.key, v.neuron_slice, memory_io)


        # Build synapsepopulations
        for pop, vertices in iteritems(pop_synapse_vertices):
            # Create a spinnaker population
            with pop.create_spinnaker_synapse_population():
                # Expand any incoming connections
                pop.expand_incoming_connection()
                
                # Loop through vertices
                '''
                for v in vertices:
                    # Get placement and allocation
                    vertex_placement = placements[v]
                    vertex_allocation = allocations[v]

                    # Get core this vertex should be run on 
                    core = vertex_allocation[machine.Cores]
                    assert (core.stop - core.start) == 1
                    
                    # Select placed chip
                    with machine_controller(x=vertex_placement[0], y=vertex_placement[1]):
                        # Allocate a suitable memory block for this vertex and get memory io
                        # **NOTE** this is tagged by core
                        memory_io = machine_controller.sdram_alloc_as_io(
                            pop.spinnaker_population().get_size(v.neuron_slice), tag=core.start)
                        print("\tMemory begins at %08x" % memory_io.address)
                        
                        # Write the vertex to file
                        pop.spinnaker_population().write_to_file(v.key, v.neuron_slice, memory_io)
                '''
        # Load routing tables and applications
        print("Loading routing tables")
        machine_controller.load_routing_tables(routing_tables)
        print("Loading applications")
        machine_controller.load_application(application_map)
        
state = State()
