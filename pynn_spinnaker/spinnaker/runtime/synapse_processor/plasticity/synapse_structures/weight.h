#pragma once

// Standard includes
#include <cstdint>

//-----------------------------------------------------------------------------
// SynapseProcessor::Plasticity::SynapseStructure::Weight
//-----------------------------------------------------------------------------
namespace SynapseProcessor
{
namespace Plasticity
{
namespace SynapseStructure
{
template<typename W, typename WeightState>
class Weight
{
public:
  //-----------------------------------------------------------------------------
  // Typedefines
  //-----------------------------------------------------------------------------
  typedef W PlasticSynapse;

  //-----------------------------------------------------------------------------
  // FinalState
  //-----------------------------------------------------------------------------
  class FinalState
  {
  public:
    //-----------------------------------------------------------------------------
    // Public API
    //-----------------------------------------------------------------------------
    W GetWeight() const
    {
      return m_Weight;
    }

    PlasticSynapse GetPlasticSynapse() const
    {
      return m_Weight;
    }

  private:
    FinalState(W weight) : m_Weight(weight)
    {
    }

    //-----------------------------------------------------------------------------
    // Members
    //-----------------------------------------------------------------------------
    W m_Weight;
  };

  Weight(PlasticSynapse plasticSynapse) : m_WeightState(plasticSynapse)
  {
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  void ApplyDepression(int32_t depression, const Additive<W> &weightDependence)
  {
    m_WeightState.ApplyDepression(depression, weightDependence);
  }

  void ApplyPotentiation(int32_t potentiation, const Additive<W> &weightDependence)
  {
    m_WeightState.ApplyPotentiation(depression, weightDependence);
  }

  FinalState CalculateFinalState(const Additive<W> &weightDependence) const
  {
    return FinalState(m_WeightState.CalculateFinalWeight(weightDependence));
  }
  
private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  WeightState m_WeightState;
};
} // SynapseStructure
} // Plasticity
} // SynapseProcessor