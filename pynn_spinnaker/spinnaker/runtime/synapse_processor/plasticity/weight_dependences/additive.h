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
  // Typedefines
  //-----------------------------------------------------------------------------
  typedef W Weight;

  //-----------------------------------------------------------------------------
  // WeightState
  //-----------------------------------------------------------------------------
  class WeightState
  {
  public:
    WeightState(Weight weight) : m_InitialWeight(weight), m_Potentiation(0), m_Depression(0)
    {
    }

    //-----------------------------------------------------------------------------
    // Public API
    //-----------------------------------------------------------------------------
    void ApplyDepression(S2011 depression, const Additive<Weight> &)
    {
      m_Depression += depression;
    }

    void ApplyPotentiation(S2011 potentiation, const Additive<Weight> &)
    {
      m_Potentiation += potentiation;
    }

    Weight CalculateFinalWeight(const Additive<Weight> &weightDependence) const
    {
      // Scale potentiation and depression and combine together
      int32_t weightChange = __smulbb(m_Potentiation, weightDependence.m_A2Plus);
      weightChange = __smlabb(m_Depression, weightDependence.m_MinusA2Minus, weightChange);
      weightChange >>= 11;

      return (Weight)(m_InitialWeight + weightChange);
    }

  private:
    //-----------------------------------------------------------------------------
    // Members
    //-----------------------------------------------------------------------------
    int32_t m_InitialWeight;

    S2011 m_Potentiation;
    S2011 m_Depression;
  };

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  // Minimum and maximum synaptic weight in runtime weight format
  int32_t m_MinWeight;
  int32_t m_MaxWeight;

  // Potentiation and depression scaling factors in runtime weight format
  int32_t m_A2Plus;
  int32_t m_MinusA2Minus;
};
} // WeightDependences
} // Plasticity
} // SynapseProcessor