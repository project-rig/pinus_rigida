#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "spinnaker.h"

//-----------------------------------------------------------------------------
// Common::ExpDecayLUT
//-----------------------------------------------------------------------------
namespace Common
{
template<unsigned int NumEntries, unsigned int Shift>
class ExpDecayLUT
{
public:
  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  void ReadSDRAMData(uint32_t *&inputPointer)
  {
     // Pad to number of words
    const uint32_t numWords = (NumEntries / 2) + (((NumEntries & 1) != 0) ? 1 : 0);

    // Copy entries to LUT
    spin1_memcpy(m_LUT, inputPointer, sizeof(int16_t) * NumEntries);

    // Advance word-aligned input pointer
    inputPointer += numWords;
  }

  int32_t Get(unsigned int t) const
  {
    // Calculate lut index
    unsigned int index = t >> Shift;

    // Return value from LUT
    return (index < NumEntries) ? m_LUT[index] : 0;
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  int16_t m_LUT[NumEntries];
};
} // Common