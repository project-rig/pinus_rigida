#pragma once

// Common includes
#include "../../../common/spike_input_buffer.h"

// Synapse processor includes
#include "../../key_lookup_binary_search.h"
#include "../../ring_buffer.h"
#include "../../synaptic_word.h"

namespace SynapseProcessor
{
//-----------------------------------------------------------------------------
// Typedefines
//-----------------------------------------------------------------------------
typedef Common::SpikeInputBufferBase<256> SpikeInputBuffer;

typedef SynapticWordBase<uint32_t, uint16_t, 3, 10> SynapticWord;
typedef RingBufferBase<uint32_t, SynapticWord> RingBuffer;

typedef KeyLookupBinarySearch<10> KeyLookup;
};