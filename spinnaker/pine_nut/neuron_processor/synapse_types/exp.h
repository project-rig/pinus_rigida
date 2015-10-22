#pragma once

// Common includes
#include "../../common/fixed_point_number.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// NeuronProcessor::NeuronModels::IFCurr
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
namespace NeuronModels
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
    S1516 m_ESynExc;

    // Inhibitory input current
    S1516 m_ISynInh;
  };

  //-----------------------------------------------------------------------------
  // ImmutableState
  //-----------------------------------------------------------------------------
  struct ImmutableState
  {
    // Excitatory decay constants
    S015 m_ExpTauSynE;

    // Inhibitory decay constant
    S015 m_ExpTauSynI;
  };

  //-----------------------------------------------------------------------------
  // Static methods
  //-----------------------------------------------------------------------------
  static inline S1516 GetExcInput(const MutableState &mutableState, const ImmutableState &) const
  {
    return mutableState.m_ESynExc;
  }

  static inline S1516 GetInhInput(const MutableState &mutableState, const ImmutableState &) const
  {
    return mutableState.m_ISynInh;
  }

  static inline void Shape(MutableState &mutableState, const ImmutableState &immutableState)
  {
    //mutableState.m_ESynExc
  }

};
} // NeuronModels
} // NeuronProcessor