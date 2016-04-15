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
namespace SynapseStructures
{
template<typename W>
class Weight
{
public:
  //-----------------------------------------------------------------------------
  // Typedefines
  //-----------------------------------------------------------------------------
  typedef W WeightDependence;
  typedef typename WeightDependence::Weight PlasticSynapse;

  //-----------------------------------------------------------------------------
  // FinalState
  //-----------------------------------------------------------------------------
  class FinalState
  {
  public:
    FinalState(typename WeightDependence::Weight weight) : m_Weight(weight)
    {
    }

    //-----------------------------------------------------------------------------
    // Public API
    //-----------------------------------------------------------------------------
    typename WeightDependence::Weight GetWeight() const
    {
      return m_Weight;
    }

    PlasticSynapse GetPlasticSynapse() const
    {
      return m_Weight;
    }

  private:
    //-----------------------------------------------------------------------------
    // Members
    //-----------------------------------------------------------------------------
    typename WeightDependence::Weight m_Weight;
  };

  Weight(PlasticSynapse plasticSynapse) : m_WeightState(plasticSynapse)
  {
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  void ApplyDepression(int32_t depression, const WeightDependence &weightDependence)
  {
    m_WeightState.ApplyDepression(depression, weightDependence);
  }

  void ApplyPotentiation(int32_t potentiation, const WeightDependence &weightDependence)
  {
    m_WeightState.ApplyPotentiation(potentiation, weightDependence);
  }

  FinalState CalculateFinalState(const WeightDependence &weightDependence) const
  {
    return FinalState(m_WeightState.CalculateFinalWeight(weightDependence));
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  typename WeightDependence::WeightState m_WeightState;
};
} // SynapseStructure
} // Plasticity
} // SynapseProcessor