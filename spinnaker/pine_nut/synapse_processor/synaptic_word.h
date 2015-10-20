#pragma once

// Standard includes
#include <cstdint>

namespace SynapseProcessor
{
//             |       Weights       |       Delay        |      Index         |
//             |---------------------|--------------------|--------------------|
// Bit count   | SYNAPSE_WEIGHT_BITS | SYNAPSE_DELAY_BITS | SYNAPSE_INDEX_BITS |
//             |---------------------|--------------------|--------------------|

//-----------------------------------------------------------------------------
// SynapticWordBase
//-----------------------------------------------------------------------------
template<typename T, typename W, unsigned int D, unsigned int I>
class SynapticWordBase
{
public:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const T NumDelayBits = D;
  static const T NumIndexBits = I;
  static const T DelayMask = ((1 << NumDelayBits) - 1);
  static const T IndexMask = ((1 << NumIndexBits) - 1);

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  T GetIndex() const{ return (m_Word & IndexMask); }
  T GetDelay() const{ return (m_Word & DelayMask); }
  W GetWeight() const{ return (W)(m_Word >> (sizeof(T) - sizeof(W))); }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  T m_Word;
};
} // SynapseProcessor