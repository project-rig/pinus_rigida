#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../../common/log.h"

//-----------------------------------------------------------------------------
// SynapseProcessor::SynapseTypes::STDP
//-----------------------------------------------------------------------------
namespace SynapseProcessor
{
namespace SynapseTypes
{
class STDP
{
public:
  template<typename F, typename E>
  static bool ProcessRow(uint tick, uint32_t (&dmaBuffer)[MaxRowWords],
                         F applyInputFunction, E addDelayRowFunction)
  {
  }

  static unsigned int GetRowWords(unsigned int rowSynapses)
  {
    // Three header word and a synapse
    return 3 + ((rowSynapses * sizeof(T)) / 4);
  }
};
} // SynapseTypes
} // SynapseProcessor