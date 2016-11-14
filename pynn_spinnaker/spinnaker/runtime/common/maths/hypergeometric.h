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
  uint32_t Hypergeom(uint32_t ngood, uint32_t nbad, uint32_t nsample, MarsKiss64 &rng);
} // Maths
} // Common
