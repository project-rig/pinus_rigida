#pragma once

// Standard includes
#include <cstdint>

//-----------------------------------------------------------------------------
// SynapseProcessor::SynapseTypes::Static
//-----------------------------------------------------------------------------
namespace SynapseProcessor
{
namespace SynapseTypes
{
template<typename S>
class Static
{
public:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  // One word for a synapse-count and 1024 synapses
  static const unsigned int MaxRowWords = 1025;
  
  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  template<typename I>
  static bool ProcessRow(uint tick, uint32_t (&dmaBuffer)[MaxRowWords],
                         I applyInputFunction)
  {
    register S *synapticWords = (S*)&dmaBuffer[1];
    register uint32_t count = dmaBuffer[0];

    for(; count > 0; count--)
    {
      // Get the next 32 bit word from the synaptic_row
      // (should autoincrement pointer in single instruction)
      S synapticWord = *synapticWords++;

      // Add weight to ring-buffer
      applyInputFunction(synapticWord.GetDelay() + tick, 
        synapticWord.GetIndex(), synapticWord.GetWeight());
    }
    
    return true;
  }
};
} // SynapseTypes
} // SynapseProcessor