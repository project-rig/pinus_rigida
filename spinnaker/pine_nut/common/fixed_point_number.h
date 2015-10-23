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
  typedef int32_t S1615;
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

  inline S1615 MulS1615(S1615 a, S1615 b)
  {
    return Mul<int32_t, int64_t, 15>(a, b);
  }
}
};  // namespace Common