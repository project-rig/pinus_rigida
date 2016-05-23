# Import modules
import pytest
from pynn_spinnaker.spinnaker import utils


@pytest.mark.parametrize(
    "input_slice, neuron_slice, expected_offset_bytes, expected_num_neurons, expected_start_neuron",
    [(utils.UnitStrideSlice(0, 256), utils.UnitStrideSlice(0, 512), 0, 256, 0),
    (utils.UnitStrideSlice(256, 512), utils.UnitStrideSlice(0, 512), 0, 256, 256),
    (utils.UnitStrideSlice(0, 512), utils.UnitStrideSlice(0, 256), 0, 256, 0),
    (utils.UnitStrideSlice(0, 512), utils.UnitStrideSlice(256, 512), 256 * 4, 256, 0),
    ])
def test_input_vertex_get_input_buffers(input_slice, neuron_slice,
                            expected_offset_bytes, expected_num_neurons, expected_start_neuron):
    # Create input vertex
    input_vertex = utils.InputVertex(input_slice, 0)

    # Setup other input buffer properties
    input_vertex.weight_fixed_point = 28
    input_vertex.out_buffers = [0x100, 0x200]

    # Get input buffer for neuron slice
    input_buffer = input_vertex.get_in_buffer(neuron_slice)

    # Check offsets
    assert input_buffer.pointers[0] == input_vertex.out_buffers[0] + expected_offset_bytes
    assert input_buffer.pointers[1] == input_vertex.out_buffers[1] + expected_offset_bytes

    # Check num neurons
    assert input_buffer.num_neurons == expected_num_neurons

    # Check start neuron
    assert input_buffer.start_neuron == expected_start_neuron

def test_input_vertex_non_overlapping_slices():
    with pytest.raises(AssertionError):
        # Create input vertex
        input_vertex = utils.InputVertex(utils.UnitStrideSlice(0, 256), 0)

        # Setup other input buffer properties
        input_vertex.weight_fixed_point = 28
        input_vertex.out_buffers = [0x100, 0x200]

        input_vertex.get_in_buffer(utils.UnitStrideSlice(512, 1024))


@pytest.mark.parametrize(
    "slice_a, slice_b, expected_overlap",
    [(utils.UnitStrideSlice(0, 10), utils.UnitStrideSlice(5, 15), True),
     (utils.UnitStrideSlice(0, 20), utils.UnitStrideSlice(10, 15), True),
     (utils.UnitStrideSlice(0, 10), utils.UnitStrideSlice(10, 20), False),
     (utils.UnitStrideSlice(0, 5), utils.UnitStrideSlice(10, 20), False)
     ])
def test_unit_strided_slice_overlap(slice_a, slice_b, expected_overlap):
    assert slice_a.overlaps(slice_b) == expected_overlap
    assert slice_b.overlaps(slice_a) == expected_overlap
