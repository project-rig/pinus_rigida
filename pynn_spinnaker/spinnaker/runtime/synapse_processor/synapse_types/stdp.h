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
template<typename C, typename W, unsigned int D, unsigned int I,
         typename TimingDependence, typename WeightDependence,
         unsigned int T>
class STDP
{
public:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  // One word for a synapse-count and 1024 synapses
  static const unsigned int MaxRowWords = 1025;

  //-----------------------------------------------------------------------------
  // Public methods
  //-----------------------------------------------------------------------------
  template<typename F, typename E>
  bool ProcessRow(uint tick, uint32_t (&dmaBuffer)[MaxRowWords], bool flush,
                  F applyInputFunction, E addDelayRowFunction)
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "\tProcessing STDP row with %u synapses",
              dmaBuffer[0]);

    // If this row has a delay extension, call function to add it
    if(dmaBuffer[1] != 0)
    {
      addDelayRowFunction(dmaBuffer[1] + tick, dmaBuffer[2]);
    }

    C *controlWords = //(T*)&dmaBuffer[3];
    
    uint32_t count = dmaBuffer[0];
    for(; count > 0; count--)
    {
      // Get the next control word from the synaptic_row
      // (should autoincrement pointer in single instruction)
      uint32_t controlWord = *controlWords++;

      // Add weight to ring-buffer
      applyInputFunction(GetDelay(controlWord) + tick,
        GetIndex(controlWord), GetWeight(synapticWord));
    }

    return true;
  }

  unsigned int GetRowWords(unsigned int rowSynapses)
  {
    // Three header word and a synapse
    //return 3 + ((rowSynapses * sizeof(T)) / 4);
  }

private:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const C DelayMask = ((1 << D) - 1);
  static const C IndexMask = ((1 << I) - 1);

  //-----------------------------------------------------------------------------
  // Private static methods
  //-----------------------------------------------------------------------------
  static C GetIndex(C word){ return (word & IndexMask); }
  static C GetDelay(C word){ return ((word >> I) & DelayMask); }

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  TimingDependence m_TimingDependence;
  WeightDependence m_WeightDependence;

  PostEventHistory<TimingDependence::PostTrace, T> m_PostEventHistory[MaxNeurons];
};
} // SynapseTypes
} // SynapseProcessor