#pragma once

// Common includes
#include "rig_cpp_common/fixed_point_number.h"

// Forward declarations
namespace Common
{
  namespace Random
  {
    class MarsKiss64;
  }
}

// Namespaces
using namespace Common::FixedPointNumber;
using namespace Common::Random;

//-----------------------------------------------------------------------------
// Common::Maths
//-----------------------------------------------------------------------------
namespace Common
{
namespace Maths
{
  uint32_t Binomial(uint32_t n, S1615 p, MarsKiss64 &rng);

  uint32_t Binomial(uint32_t n, uint32_t numerator, uint32_t denominator, MarsKiss64 &rng);
} // Maths
} // Common
