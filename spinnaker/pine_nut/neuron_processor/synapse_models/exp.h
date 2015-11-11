#pragma once

// Common includes
#include "../../common/fixed_point_number.h"
#include "../../common/spinnaker.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// NeuronProcessor::SynapseModels::Exp
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
namespace SynapseModels
{
class Exp
{
public:
  //-----------------------------------------------------------------------------
  // MutableState
  //-----------------------------------------------------------------------------
  struct MutableState
  {
    // Excitatory input current
    S1615 m_ISynExc;

    // Inhibitory input current
    S1615 m_ISynInh;
  };

  //-----------------------------------------------------------------------------
  // ImmutableState
  //-----------------------------------------------------------------------------
  struct ImmutableState
  {
    // Excitatory decay constants
    S1615 m_ExpTauSynExc;

    // Excitatory initial value
    S1615 m_InitE;

    // Inhibitory decay constant
    S1615 m_ExpTauSynInh;

    S1615 m_InitI;
  };

  //-----------------------------------------------------------------------------
  // Static methods
  //-----------------------------------------------------------------------------
  static inline void ApplyInput(MutableState &mutableState, const ImmutableState &immutableState, S1615 input, unsigned int receptorType)
  {
    // Apply input to correct receptor
    // **TODO** Are m_ExpTauSynExc and m_ExpTauSynInh always going to be 16 bits? If so, can we use 16x32 DSP multiply
    if(receptorType == 0)
    {
      mutableState.m_ISynExc += MulS1615(input, immutableState.m_InitE);
    }
    else
    {
      mutableState.m_ISynInh += MulS1615(input, immutableState.m_InitI);
    }
  }

  static inline S1615 GetExcInput(const MutableState &mutableState, const ImmutableState &)
  {
    return mutableState.m_ISynExc;
  }

  static inline S1615 GetInhInput(const MutableState &mutableState, const ImmutableState &)
  {
    return mutableState.m_ISynInh;
  }

  static inline void Shape(MutableState &mutableState, const ImmutableState &immutableState)
  {
    // Decay both currents
    // **TODO** Are m_ExpTauSynExc and m_ExpTauSynInh always going to be 16 bits? If so, can we use 16x32 DSP multiply
    mutableState.m_ISynExc = MulS1615(mutableState.m_ISynExc, immutableState.m_ExpTauSynExc);
    mutableState.m_ISynInh = MulS1615(mutableState.m_ISynInh, immutableState.m_ExpTauSynInh);
  }

  static void Print(char *stream, const MutableState &mutableState, const ImmutableState &immutableState);
};
} // NeuronModels
} // NeuronProcessor