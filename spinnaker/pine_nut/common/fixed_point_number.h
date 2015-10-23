#pragma once

// Standard includes
#include <cstdint>

//-----------------------------------------------------------------------------
// Common::FixedPointNumber
//-----------------------------------------------------------------------------
namespace Common
{
namespace FixedPointNumber
{
  //-----------------------------------------------------------------------------
  // Typedefines
  //-----------------------------------------------------------------------------
  typedef int32_t S1615;

  //-----------------------------------------------------------------------------
  // Functions
  //-----------------------------------------------------------------------------
  template<typename Type, typename IntermediateType, unsigned int FractionalBits>
  inline Type Mul(Type a, Type b)
  {
    IntermediateType m = a * b;
    return (Type)(m >> FractionalBits);
  }

  inline S1615 MulS1615(S1615 a, S1615 b)
  {
    return Mul<int32_t, int64_t, 16>(a, b);
  }
}
};  // namespace Common