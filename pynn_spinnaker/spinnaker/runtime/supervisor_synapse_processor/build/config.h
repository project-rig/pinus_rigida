#pragma once

// Common includes
#include "../../common/spike_input_buffer.h"
namespace SupervisorSynapseProcessor
{
  typedef Common::SpikeInputBufferBase<256> SpikeInputBuffer;
}

#include "../../common/key_lookup_binary_search.h"
namespace SupervisorSynapseProcessor
{
  typedef Common::KeyLookupBinarySearch<10> KeyLookup;
}