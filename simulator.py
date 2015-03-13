# Import modules
import itertools
import os
from rig import machine

# Import classes
from pyNN import common
from rig.bitfield import BitField
from rig.machine_control.machine_controller import MachineController, MemoryIO
from rig.netlist import Net
from rig.place_and_route import wrapper

name = "SpiNNaker"

def generate_nets_and_keys(pre_pop, post, population_vertices):
    nets = []
    net_keys = []
    for pre_vert in population_vertices[pre_pop]:
        # Add key to list
        net_keys.append((pre_vert.key, pre_vert.mask))
        
        # If post-synaptic population is an assembly
        if isinstance(post, common.Assembly):
            # Add the vertices that make up each 
            # Population in assembly to list
            sink_vertices = []
            for post_pop in post.populations:
                sinks.extend(population_vertices[post_pop])
            nets.append(Net(pre_vert, sink_vertices))

        # Otherwise, just add a single net connecting pre-vertex 
        # To all vertices in post-synaptic population
        # **TODO** population views
        else:
            nets.append(Net(pre_vert, population_vertices[post]))

    return nets, net_keys

#------------------------------------------------------------------------------
# Vertex
#------------------------------------------------------------------------------
class Vertex:
    def __init__(self, parent_keyspace, vertex_slice, population_index, vertex_index):
        self.vertex_slice = vertex_slice
        self.keyspace = parent_keyspace(population_index=population_index, 
            vertex_index=vertex_index)
    
    @property
    def key(self):
        return self.keyspace.get_value(tag="routing")
    
    @property
    def mask(self):
        return self.keyspace.get_mask(tag="routing")

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
        self._build()
        
        self.t += simtime
        self.running = True
        
    def run_until(self, tstop):
        # Build data
        self._build()
        
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
        duration_timesteps = int(round(float(runtime_ms) / float(self.dt)))
        
        print("Simulating for %u %uus timesteps using a hardware timestep of %uus" % 
            (duration_timesteps, simulation_timestep_us, hardware_timestep_us))
        
        # Create a 32-bit keyspace
        keyspace = BitField(32)
        keyspace.add_field("population_index", tags="routing")
        keyspace.add_field("vertex_index", tags="routing")
        keyspace.add_field("neuron_id", length=10, start_at=0, tags="application")
        
        # Get directory of backend
        backend_dir = os.path.dirname(__file__)
        
        print("Partitioning vertices")
        # Loop through populations
        population_vertices = {}
        vertex_applications = {}
        vertex_resources = {}
        for pidx, pop in enumerate(self.populations):  
            # Partition population to get slices and resources for each vertex
            slices, resources = pop.partition()
            
            # Build vertices by allocating a keyspace for each vertex
            vertices = [Vertex(keyspace, vslice, pidx, vidx) for vidx, vslice in enumerate(slices)]
            
            # Add resultant list of vertex tuples to dictionary
            population_vertices[pop] = vertices
            
            # **TEMP** get application from celltype
            # **TODO* path to aplx, take STDP name munging into account
            application = os.path.join(backend_dir, "model_binaries", pop.celltype.__class__.__name__ + ".aplx")
            print application
            
            # Loop through vertices and their correspondign resources again
            for v, r in zip(vertices, resources):
                # Add application to dictionary
                vertex_applications[v] = application
                
                # Add resources to dictionary
                vertex_resources[v] = r
        
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
                        pre_pop, proj.post, population_vertices)
                    
                    # Add to global lists
                    nets.extend(vertex_nets)
                    net_keys.update(zip(vertex_nets, vertex_net_keys))
            # Otherwise, it's a single population
            # **TODO** population view
            else:
                # Generate list of nets and their key coming from this population
                vertex_nets, vertex_net_keys = generate_nets_and_keys(
                    proj.pre, proj.post, population_vertices)
                
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
        
        # Build populations
        for pop, vertices in population_vertices.iteritems():
            # Create a spinnaker population
            with pop.create_spinnaker_population(simulation_timestep_us, 
                                                 hardware_timestep_us, 
                                                 duration_timesteps):
                # Expand any incoming connections
                pop.expand_incoming_connection()
                
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
                        memory_io = machine_controller.sdram_alloc_as_io(
                            pop.spinnaker_population().get_size(v.vertex_slice), tag=core.start)
                        print("\tMemory begins at %08x" % memory_io.address)
                        
                        # Write the vertex to file
                        pop.spinnaker_population().write_to_file(v.key, v.vertex_slice, memory_io)
        
        # Load routing tables and applications
        print("Loading routing tables")
        machine_controller.load_routing_tables(routing_tables)
        print("Loading applications")
        machine_controller.load_application(application_map)
        
        
        
state = State()
