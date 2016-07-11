#pragma once

// Common includes
#include "../../../common/spike_input_buffer.h"
namespace SynapseProcessor
{
  typedef Common::SpikeInputBufferBase<256> SpikeInputBuffer;
}

// Synapse processor includes
#include "../../../common/key_lookup_binary_search.h"
namespace SynapseProcessor
{
  typedef Common::KeyLookupBinarySearch<10> KeyLookup;
}


#include "../../synapse_types/static.h"
namespace SynapseProcessor
{
  typedef SynapseTypes::Static<uint32_t, uint16_t, 3, 10> SynapseType;
}


#include "../../ring_buffer.h"
namespace SynapseProcessor
{
  typedef RingBufferBase<uint32_t, 3, 10> RingBuffer;
}

#include "../../delay_buffer.h"
namespace SynapseProcessor
{
  typedef DelayBufferBase<10> DelayBuffer;
}
