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
  typedef uint32_t U032;
  typedef int16_t S511;

  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const S1615 S1615One = (1 << 15);
  static const S511 S511One = (1 << 11);

  //-----------------------------------------------------------------------------
  // Functions
  //-----------------------------------------------------------------------------
  template<typename Type, typename IntermediateType, unsigned int FractionalBits>
  inline Type Mul(Type a, Type b)
  {
    IntermediateType m = (IntermediateType)a * (IntermediateType)b;
    return (Type)(m >> FractionalBits);
  }

  inline S1615 MulS1615(S1615 a, S1615 b)
  {
    return Mul<int32_t, int64_t, 15>(a, b);
  }

  inline U032 MulU032(U032 a, U032 b)
  {
    return Mul<uint32_t, uint64_t, 32>(a, b);
  }

  inline int32_t MulS511(S511 a, S511 b)
  {
    // Multiply lower 16-bits of a and b together
    int32_t mul = __smulbb(a, b);

    // Shift down
    return (mul >> 11);
}
}
};  // namespace Common