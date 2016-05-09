#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "arm_intrinsics.h"

// Namespaces
using namespace Common::ARMIntrinsics;

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
  typedef int32_t S2011;

  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const S1615 S1615One = (1 << 15);
  static const S2011 S2011One = (1 << 11);

  //-----------------------------------------------------------------------------
  // Functions
  //-----------------------------------------------------------------------------
  template<typename Type, typename IntermediateType, unsigned int FractionalBits>
  inline Type Mul(Type a, Type b)
  {
    IntermediateType m = (IntermediateType)a * (IntermediateType)b;
    return (Type)(m >> FractionalBits);
  }

  template<unsigned int FractionalBits>
  inline int32_t Mul16(int32_t a, int32_t b)
  {
    // Multiply lower 16-bits of a and b together
    int32_t mul = __smulbb(a, b);

    // Shift down
    return (mul >> FractionalBits);
  }

  inline S1615 MulS1615(S1615 a, S1615 b)
  {
    return Mul<int32_t, int64_t, 15>(a, b);
  }

  inline U032 MulU032(U032 a, U032 b)
  {
    return Mul<uint32_t, uint64_t, 32>(a, b);
  }

  inline S1615 MulS1615U032(S1615 a, U032 b)
  {
    int64_t m = (int64_t)a * (int64_t)b;
    return (S1615)(m >> 32);
  }

  inline S2011 Mul16S2011(S2011 a, S2011 b)
  {
    return Mul16<11>(a, b);
  }
}
};  // namespace Common