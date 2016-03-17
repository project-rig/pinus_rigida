#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../../../common/fixed_point_number.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// SynapseProcessor::Plasticity::WeightDependences::Additive
//-----------------------------------------------------------------------------
namespace SynapseProcessor
{
namespace Plasticity
{
namespace WeightDependences
{
template<typename W>
class Additive
{
public:
  //-----------------------------------------------------------------------------
  // WeightState
  //-----------------------------------------------------------------------------
  class WeightState
  {
  public:
    WeightState(W weight) : m_InitialWeight(weight), m_Potentiation(0), m_Depression(0)
    {
    }

    //-----------------------------------------------------------------------------
    // Public API
    //-----------------------------------------------------------------------------
    void ApplyDepression(int32_t depression)
    {
      m_Depression += depression;
    }

    void ApplyPotentiation(int32_t potentiation)
    {
      m_Potentiation += potentiation;
    }

    W CalculateFinalWeight() const
    {
      // Scale potentiation and depression and combine together
      int32_t weightChange = __smulbb(m_Potentiation, Additive<Weight>::m_A2Plus);
      weightChange = __smlabb(m_Depression, Additive<Weight>::m_MinusA2Minus, weightChange);
      weightChange >>= 11;

      return (W)(m_InitialWeight + weightChange);
    }

    //-----------------------------------------------------------------------------
    // Static API
    //-----------------------------------------------------------------------------

  private:
    //-----------------------------------------------------------------------------
    // Members
    //-----------------------------------------------------------------------------
    int32_t m_InitialWeight;

    int32_t m_Potentiation;
    int32_t m_Depression;
  };

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  static int32_t m_MinWeight;
  static int32_t m_MaxWeight;

  static int32_t m_A2Plus;
  static int32_t m_MinusA2Minus;
};
} // WeightDependences
} // Plasticity
} // SynapseProcessor