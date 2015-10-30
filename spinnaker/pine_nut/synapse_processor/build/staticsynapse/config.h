#pragma once

// Common includes
#include "../../../common/spike_input_buffer.h"
namespace SynapseProcessor
{
  typedef Common::SpikeInputBufferBase<256> SpikeInputBuffer;
}

// Synapse processor includes
#include "../../key_lookup_binary_search.h"
namespace SynapseProcessor
{
  typedef KeyLookupBinarySearch<10> KeyLookup;
}

#include "../../synaptic_word.h"
namespace SynapseProcessor
{
  typedef SynapticWordBase<uint32_t, uint16_t, 3, 10> SynapticWord;
}

#include "../../ring_buffer.h"
namespace SynapseProcessor
{
  typedef RingBufferBase<uint32_t, SynapticWord> RingBuffer;
}

#include "../../synapse_types/static.h"
namespace SynapseProcessor
{
  typedef SynapseTypes::Static<SynapticWord> SynapseType;
}
