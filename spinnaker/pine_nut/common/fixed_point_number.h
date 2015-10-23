#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "arm_intrinsics.h"

//-----------------------------------------------------------------------------
// Common
//-----------------------------------------------------------------------------
namespace Common
{

//-----------------------------------------------------------------------------
// FixedPointNumber
//-----------------------------------------------------------------------------
/*template<typename Type, unsigned int FractionalBits>}
class FixedPointNumber
{
public:
  FixedPointNumber(FixedPointNumber<Type, FractionalBits const& other) : FixedPointNumber(other.m_Value){}

  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const FixedPointNumber<Type, FractionalBits> One = FixedPointNumber<Type, FractionalBits>(1 << FractionalBits);

private:
  FixedPointNumber(Type value) : m_Value(value){}

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  Type m_Value;
};*/

namespace FixedPointNumber
{
  //-----------------------------------------------------------------------------
  // Typedefines
  //-----------------------------------------------------------------------------
  typedef int32_t S1516;
  typedef int16_t S015;

  //-----------------------------------------------------------------------------
  // Functions
  //-----------------------------------------------------------------------------
  template<typename Type, typename IntermediateType, unsigned int FractionalBits>
  inline Type Mul(Type a, Type b)
  {
    IntermediateType m = a * b;
    return (Type)(m >> FractionalBits);
  }

  inline S1516 MulS1616_S015(S1516 a, S1516 b)
  {
    return ARMIntrinsics::__smulwb(a, b);
  }

  inline S1516 MulS1516_S1516(S1516 a, S1516 b)
  {
    return Mul<int32_t, int64_t, 16>(a, b);
  }
}
};  // namespace Common