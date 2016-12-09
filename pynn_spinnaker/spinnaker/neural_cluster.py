# Import modules
import enum
import itertools
import logging
import numpy as np
import regions
from rig import machine

# Import classes
from collections import defaultdict
from rig_cpp_common.regions import Profiler, Statistics, System
from rig_cpp_common.utils import Args

# Import functions
from rig_cpp_common.utils import load_regions
from six import iteritems
from utils import (calc_bitfield_words, calc_slice_bitfield_words,
                   get_model_executable_filename, split_slice)

logger = logging.getLogger("pynn_spinnaker")


# ----------------------------------------------------------------------------
# Regions
# ----------------------------------------------------------------------------
class Regions(enum.IntEnum):
    """Region names, corresponding to those defined in `neuron_processor.h`"""
    system = 0
    neuron = 1
    synapse = 2
    input_buffer = 3
    back_prop_output = 4
    flush = 5
    intrinsic_plasticity = 6
    spike_recording = 7
    analogue_recording_0 = 8
    analogue_recording_1 = 9
    analogue_recording_2 = 10
    analogue_recording_3 = 11
    analogue_recording_start = analogue_recording_0
    analogue_recording_end = analogue_recording_3 + 1
    profiler = analogue_recording_end
    statistics = analogue_recording_end + 1


# ----------------------------------------------------------------------------
# Vertex
# ----------------------------------------------------------------------------
class Vertex(object):
    """A vertex represents a subset of the neurons within a :py:class:`NeuralCluster`.
    These have been partitioned so that these neurons can be simualated using
    a single SpiNNaker core and have been assigned a keyspace.

    Attributes
    ----------
    input_verts : [:py:class:`~pynn_spinnaker.spinnaker.utils.InputVertex`]
        List of input vertices which provide input via SDRAM buffers to this
        neuron vertex.
    vert_index : int
        Index of this vertex within the :py:class:`NeuralCluster` - used when
        connectivity is being built on chip using
        :py:class:`pynn_spinnaker.spinnaker.regions.connection_builder` to
        locate the 'tile' within a synaptic matrix
        a particular connection is in.
    region_memory : {name: file-like}
        When the vertex has been loaded onto the SpiNNaker machine this
    """
    def __init__(self, parent_keyspace, neuron_slice, pop_index, vert_index):
        """
        Parameters
        ----------
        parent_keyspace : :py:class:`rig.bitfield.BitField`
            Keyspace from which keys for spikes and 'flush' events emitted
            by this vertex should be allocated.
        neuron_slice : :py:class:`~pynn_spinnaker.spinnaker.utils.UnitStrideSlice`
            Slice of neurons within the :py:class:`NeuralCluster` this vertex
            represents.
        pop_index : int
            Global index of the population whose neurons this vertex
            is responsible for simulating - used for generating unique keys
        vert_index : int
            Index of this vertex within the :py:class:`NeuralCluster` - used
            both for generating unique keys and in
            :py:class:`pynn_spinnaker.spinnaker.regions.connection_builder` to
            locate 'tiles' within a synaptic matrix.
        """
        self.neuron_slice = neuron_slice

        # Build child keyspaces for spike and
        # flush packets coming from this vertex
        self._spike_keyspace = parent_keyspace(pop_index=pop_index,
                                              vert_index=vert_index,
                                              flush=0)
        self._flush_keyspace = parent_keyspace(pop_index=pop_index,
                                              vert_index=vert_index,
                                              flush=1)

        self.vert_index = vert_index

        self.input_verts = []
        self.back_prop_out_buffers = None
        self.region_memory = None

    # ------------------------------------------------------------------------
    # Magic methods
    # ------------------------------------------------------------------------
    def __str__(self):
        return "<neuron slice:%s>" % (str(self.neuron_slice))

    # -----------------------------------------------"""-------------------------
    # Public methods
    # ------------------------------------------------------------------------
    def get_back_prop_in_buffer(self, post_slice):
        """Provides pointers into the buffers written by this vertex from
        which a synapse processor can obtain the postsynaptic spiking
        information required to calculate (for example) STDP weight updates.

        There are two of these buffers so, in a given timestep, a neuron
        processor writes to one and the synapse processor reads from the other.
        Each buffer contains a bit-field representation of the spiking activity
        in a single timestep.

        Parameters
        ----------
        post_slice : :py:class:`~pynn_spinnaker.spinnaker.utils.UnitStrideSlice`
            Slice of neurons which synapse processor
            requires the spiking activity for.
        Returns
        -------
        ([int], int, int, int)
            Tuple containing:
                1. List of pointers to the two buffers
                2. Length of each buffer in words
                3. Index of bit within the bit-field where processing should begin
                4. Index of bit within the bit-field where processing should stop
        """
        # Check the slices involved overlap and that this
        # neuron vertex actually has back propagation buffers
        assert post_slice.overlaps(self.neuron_slice)
        assert self.back_prop_out_buffers is not None

        # Calculate start and end bit in neuron id-space
        neuron_start_bit = max(post_slice.start, self.neuron_slice.start)
        neuron_end_bit = min(post_slice.stop, self.neuron_slice.stop)
        logger.debug("\t\t\tNeuron start bit:%u, Neuron end bit:%u",
                     neuron_start_bit, neuron_end_bit)

        # Calculate where in the buffer post_slice starts
        buffer_start_bit = neuron_start_bit - self.neuron_slice.start
        assert buffer_start_bit >= 0

        # Seperate where the buffer starts in words and bits
        buffer_start_word = buffer_start_bit // 32
        buffer_start_bit -= (buffer_start_word * 32)
        buffer_end_bit = (neuron_end_bit - neuron_start_bit) + buffer_start_bit
        buffer_num_words = calc_bitfield_words(buffer_end_bit)
        logger.debug("\t\t\tBuffer start word:%u, Buffer start bit:%u, Buffer end bit:%u, Buffer num words:%u",
                     buffer_start_word, buffer_start_word,
                     buffer_end_bit, buffer_num_words)

        # Return offset pointers into out buffers
        return (
            [b + (buffer_start_word * 4) for b in self.back_prop_out_buffers],
            buffer_num_words, buffer_start_bit, buffer_end_bit)

    # ------------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------------
    @property
    def spike_tx_key(self):
        """
        Returns
        -------
        int
            The key this vertex should use to transmit spikes.
        """
        return self._spike_keyspace.get_value(tag="transmission")

    @property
    def flush_tx_key(self):
        """
        Returns
        -------
        int
            The key this vertex should use to transmit 'flush' events.
        """
        return self._flush_keyspace.get_value(tag="transmission")

    @property
    def routing_key(self):
        """
        Returns
        -------
        int
            The key that should be used to route both spikes and 'flush'
            events from this vertex.
        """
        # Check that routing key for the spike and flush keyspace are the same
        spike_key = self._spike_keyspace.get_value(tag="routing")
        flush_key = self._flush_keyspace.get_value(tag="routing")
        assert spike_key == flush_key

        # Return the spike key (arbitarily)
        return spike_key

    @property
    def routing_mask(self):
        """
        Returns
        -------
        int
            The mask that should be used to route both spikes and 'flush'
            events from this vertex.
        """
        # Check that routing mask for the spike and flush keyspace are the same
        spike_mask = self._spike_keyspace.get_mask(tag="routing")
        flush_mask = self._flush_keyspace.get_mask(tag="routing")
        assert spike_mask == flush_mask

        # Return the spike mask (arbitarily)
        return spike_mask

# -----------------------------------------------------------------------------
# NeuralCluster
# -----------------------------------------------------------------------------
class NeuralCluster(object):
    """Neural clusters are generated from the neurons contained by a
    :py:class:`~pynn_spinnaker.Population`. They are responsible for
    converting the neuron parameters specified by PyNN into a form usable by
    neuron processors running on SpiNNaker.

    Attributes
    ----------
    regions : {:py:class:`Regions`: :py:class:`rig_cpp_common.regions.region.Region`}
        Dictionary of regions that must be written to memory for each
        neuron processor that makes up this neural cluster.
    verts : [:py:class:`Vertex`]
        List of vertices that make up this neural cluster.

    """
    # Tag names, corresponding to those defined in neuron_processor.h
    profiler_tag_names = {
        0:  "Synapse shape",
        1:  "Update neurons",
        2:  "Apply buffer",
    }

    # Names of statistics
    statistic_names = (
        "task_queue_full",        """Estimates the SDRAM required by a core simulating a slice of the
        neurons in this neural cluster.


        """
        "timer_event_overflows",
    )

    def __init__(self, pop_id, cell_type, parameters, initial_values,
                 sim_timestep_ms, timer_period_us, sim_ticks,
                 record_sample_interval, indices_to_record, config,
                 vertex_load_applications, vertex_run_applications,
                 vertex_resources, keyspace, post_synaptic_width,
                 requires_back_prop, pop_size):
        """
        Parameters
        ----------
        pop_id : integer
            Global index of the population whose neurons this vertex
            is responsible for simulating - used for generating unique keys
        """
        # Create standard regions
        self.regions = {}
        self.regions[Regions.system] = System(timer_period_us, sim_ticks)
        self.regions[Regions.neuron] = cell_type._neuron_region_class(
            cell_type, parameters, initial_values, sim_timestep_ms, pop_size)
        self.regions[Regions.back_prop_output] = regions.SDRAMBackPropOutput(
            requires_back_prop)
        self.regions[Regions.flush] = regions.Flush(config.flush_time,
                                                    sim_timestep_ms)
        self.regions[Regions.spike_recording] = regions.SpikeRecording(
            indices_to_record, sim_timestep_ms, sim_ticks)
        self.regions[Regions.statistics] = Statistics(len(self.statistic_names))

        # If cell type has any receptors i.e. any need for synaptic input
        if len(cell_type.receptor_types) > 0:
            # Add a synapse region and an input buffer
            self.regions[Regions.synapse] = regions.ParameterSpace(
                cell_type._synapse_mutable_param_map,
                cell_type._synapse_immutable_param_map,
                parameters, initial_values, pop_size,
                sim_timestep_ms=sim_timestep_ms)

            self.regions[Regions.input_buffer] = regions.InputBuffer()

         # If cell type has an intrinsic plasticity parameter map
        if hasattr(cell_type, "intrinsic_plasticity_param_map"):
            self.regions[Regions.intrinsic_plasticity] =\
                regions.HomogeneousParameterSpace(
                    cell_type._intrinsic_plasticity_param_map,
                    parameters,
                    sim_timestep_ms)

        # Assert that there are sufficient analogue
        # recording regions for this celltype's needs
        num_analogue_rec_regions = Regions.analogue_recording_end -\
            Regions.analogue_recording_start
        assert num_analogue_rec_regions >= (len(cell_type.recordable) - 1)

        # Loop through cell's non-spike recordables
        # and create analogue recording regions
        # **HACK** this assumes the first entry is spike
        for i, v in enumerate(cell_type.recordable[1:]):
            self.regions[Regions(Regions.analogue_recording_start + i)] =\
                regions.AnalogueRecording(indices_to_record, v,
                                          record_sample_interval,
                                          sim_timestep_ms, sim_ticks)

        # Add profiler region if required
        if config.num_profile_samples is not None:
            self.regions[Regions.profiler] =\
                Profiler(config.num_profile_samples)

        # Split population slice
        neuron_slices = split_slice(pop_size, post_synaptic_width)

        # Build neuron vertices for each slice,
        # allocating a keyspace for each vertex
        self.verts = [Vertex(keyspace, neuron_slice, pop_id, vert_id)
                      for vert_id, neuron_slice in enumerate(neuron_slices)]

        # Get neuron executable name
        neuron_app = get_model_executable_filename(
            "neuron_", cell_type, config.num_profile_samples is not None)

        logger.debug("\t\tNeuron application:%s", neuron_app)
        logger.debug("\t\t%u neuron vertices", len(self.verts))

        # Loop through neuron vertices and their corresponding resources
        for v in self.verts:
            # Add application to dictionary
            vertex_run_applications[v] = neuron_app

            # Estimate SDRAM usage and check
            # it's an integer as otherwise C CSA fails
            sdram = self._estimate_sdram(v.neuron_slice)
            assert isinstance(sdram, int)

            logger.debug("\t\t\tVertex %s: %u bytes SDRAM", v, sdram)

            # Add resources to dictionary
            vertex_resources[v] = {machine.Cores: 1, machine.SDRAM: sdram}

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def allocate_out_buffers(self, placements, allocations,
                             machine_controller):
        """Allocates output SDRAM buffers required for back propagation output.
        Both neural clusters and synapse clusters have output buffers the other
        needs access to so allocating these in a separate phase is necessary.

        Parameters
        ----------
        placements : {vertex: (x, y), ...}
            A dictionary from vertices to the chip coordinate produced by
            placement.
        allocations : {vertex: {resource: slice, ...}, ...}
            A dictionary from vertices to the resources allocated to it. Resource
            allocations are dictionaries from resources to a :py:class:`slice`
            defining the range of the given resource type allocated to the vertex.
            These :py:class:`slice` objects have `start` <= `end` and `step` set to
            None.
        machine_controller : :py:class:`rig.machine_control.machine_controller.MachineController`
            Machine controller used to interact with the SpiNNaker machine.
        """
        # Loop through vertices
        for v in self.verts:
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
            with machine_controller(x=vertex_placement[0],
                                    y=vertex_placement[1]):
                # If back propagation is enabled, allocate two back
                # propagation out buffers for this neuron vertex
                if self.regions[Regions.back_prop_output].enabled:
                    back_prop_buffer_bytes =\
                        calc_slice_bitfield_words(v.neuron_slice) * 4
                    v.back_prop_out_buffers = [
                        machine_controller.sdram_alloc(back_prop_buffer_bytes,
                                                       clear=True)
                        for _ in range(2)]

    def load(self, placements, allocations, machine_controller):
        """Loads the :py:class:`Vertex`s that make up this neural cluster
        onto a SpiNNaker machine.

        Parameters
        ----------
        placements : {vertex: (x, y), ...}
            A dictionary from vertices to the chip coordinate produced by
            placement.
        allocations : {vertex: {resource: slice, ...}, ...}
            A dictionary from vertices to the resources allocated to it. Resource
            allocations are dictionaries from resources to a :py:class:`slice`
            defining the range of the given resource type allocated to the vertex.
            These :py:class:`slice` objects have `start` <= `end` and `step` set to
            None.
        machine_controller : :py:class:`rig.machine_control.machine_controller.MachineController`
            Machine controller used to interact with the SpiNNaker machine.
        """
        # Loop through vertices
        for v in self.verts:
            # Get placement and allocation
            vertex_placement = placements[v]
            vertex_allocation = allocations[v]

            # Get core this vertex should be run on
            core = vertex_allocation[machine.Cores]
            assert (core.stop - core.start) == 1

            logger.debug("\t\t\tVertex %s (%u, %u, %u): Spike key:%08x, Flush key:%08x",
                            v, vertex_placement[0], vertex_placement[1],
                            core.start, v.spike_tx_key, v.flush_tx_key)

            # Select placed chip
            with machine_controller(x=vertex_placement[0],
                                    y=vertex_placement[1]):
                # Get the input buffers from each synapse vertex
                in_buffers = [
                    s.get_in_buffer(v.neuron_slice)
                    for s in v.input_verts]

                # Get regiona arguments
                region_arguments = self._get_region_arguments(
                    v.spike_tx_key, v.flush_tx_key, v.neuron_slice,
                    in_buffers, v.back_prop_out_buffers)

                # Load regions
                v.region_memory = load_regions(self.regions, region_arguments,
                                               machine_controller, core,
                                               logger)

    def read_recorded_spikes(self):
        """
        Downloads spike times recording during the preceding simulation from SpiNNaker.

        Returns
        -------
        {:py:class:`~pynn_spinnaker.spinnaker.utils.UnitStrideSlice`: {int: :py:class:`~numpy.ndarray`}}
            A dictionary mapping the slices associated with each underlying
            vertex of the neural cluster to a dictionary mapping neuron indices
            to spike times.
        """
        # Loop through all neuron vertices and read spike times into dictionary
        spike_times = {}
        region = self.regions[Regions.spike_recording]
        for v in self.verts:
            region_mem = v.region_memory[Regions.spike_recording]
            spike_times.update(region.read_spike_times(v.neuron_slice,
                                                       region_mem))
        return spike_times

    def read_recorded_signal(self, channel):
        """
        Downloads 'analogue' signals e.g. membrane voltage
        recording during the preceding simulation from SpiNNaker.

        Parameters
        ----------
        channel : int
            Index of the channel to download - This is the index of
            the 'recordable' in the cell type

        Returns
        -------
        {:py:class:`~pynn_spinnaker.spinnaker.utils.UnitStrideSlice`: {int: :py:class:`~numpy.ndarray`}}
            A dictionary mapping the slices associated with each underlying
            vertex of the neural cluster to a dictionary mapping neuron indices
            to time-varying analogue signal values.

        """
        # Get index of channelread_profile
        region_index = Regions(Regions.analogue_recording_start + channel)
        region = self.regions[region_index]

        # Loop through all neuron vertices and read signal
        signal = {}
        for v in self.verts:
            region_mem = v.region_memory[region_index]
            signal.update(region.read_signal(v.neuron_slice, region_mem))

        return signal

    def read_profile(self):
        # Get the profile recording region and
        region = self.regions[Regions.profiler]

        # Return profile data for each vertex that makes up population
        return [(v.neuron_slice.python_slice,
                 region.read_profile(v.region_memory[Regions.profiler],
                                     self.profiler_tag_names))
                for v in self.verts]

    def read_statistics(self):
        # Get the statistics recording region
        region = self.regions[Regions.statistics]

        # Read stats from all vertices
        return region.read_stats(
            [v.region_memory[Regions.statistics] for v in self.verts],
            self.statistic_names)

    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _estimate_sdram(self, vertex_slice):
        # Begin with size of spike recording region
        sdram = self.regions[Regions.spike_recording].sizeof(vertex_slice);

        # Add on size of neuron region
        sdram += self.regions[Regions.neuron].sizeof(vertex_slice)
        
        # If profiler region exists, add its size
        if Regions.profiler in self.regions:
            sdram += self.regions[Regions.profiler].sizeof()

        # Loop through possible analogue recording regions
        for t in range(Regions.analogue_recording_start,
                       Regions.analogue_recording_end):
            # If region exists, add its size to total
            if Regions(t) in self.regions:
                sdram += self.regions[Regions(t)].sizeof(vertex_slice)

        return sdram

    def _get_region_arguments(self, spike_tx_key, flush_tx_key, vertex_slice,
                              in_buffers, back_prop_out_buffers):
        region_arguments = defaultdict(Args)

        analogue_recording_regions = range(Regions.analogue_recording_start,
                                           Regions.analogue_recording_end)
        # Add vertex slice to regions that require it
        for r in itertools.chain((Regions.neuron,
                                  Regions.synapse,
                                  Regions.spike_recording),
                                 analogue_recording_regions):
            region_arguments[r] = Args(vertex_slice)

        # Add kwargs for regions that require them
        region_arguments[Regions.system].kwargs["application_words"] =\
            [spike_tx_key, flush_tx_key, len(vertex_slice)]
        region_arguments[Regions.input_buffer].kwargs["in_buffers"] =\
            in_buffers
        region_arguments[Regions.back_prop_output].kwargs["out_buffers"] =\
            back_prop_out_buffers
        return region_arguments
