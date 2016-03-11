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
class Additive
{
public:
  //-----------------------------------------------------------------------------
  // WeightState
  //-----------------------------------------------------------------------------
  struct WeightState
  {
  };

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  int32_t m_MinWeight;
  int32_t m_MaxWeight;

  int32_t m_A2Plus;
  int32_t m_A2Minus;
};
} // WeightDependences
} // Plasticity
} // SynapseProcessor