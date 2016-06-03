#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "spinnaker.h"

//-----------------------------------------------------------------------------
// Common::InverseTransformSampleLUT
//-----------------------------------------------------------------------------
namespace Common
{
template<unsigned int FixedPoint,
         typename LutType,
         typename NativeType,
         typename R>
class InverseTransformSampleLUT
{
private:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const NativeType FixedPointOne = (1 << FixedPoint);

public:
  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  void ReadSDRAMData(uint32_t *&inputPointer)
  {
    // Copy entries to LUT
    spin1_memcpy(m_LUT, inputPointer, sizeof(LutType) * FixedPointOne);

    // Advance word-aligned input pointer
    inputPointer += ((sizeof(LutType) * FixedPointOne) / sizeof(uint32_t));
  }

  int32_t Get(R &rng) const
  {
    // Pick random number in [0, 1) interval
    uint32_t random = (rng.GetNext() & (FixedPointOne - 1));

    // Return value from LUT
    return m_LUT[random];
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  LutType m_LUT[FixedPointOne];
};
} // Common