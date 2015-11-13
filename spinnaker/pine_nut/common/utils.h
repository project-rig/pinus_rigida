#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "spinnaker.h"

//-----------------------------------------------------------------------------
// Common::Utils
//-----------------------------------------------------------------------------
namespace Common
{
namespace Utils
{
// **TODO** const somewhere on inputPointer!
template<typename T>
bool AllocateCopyStructArray(unsigned int numElements, uint32_t *&inputPointer, T *&outputArray)
{
  static_assert(sizeof(T) % 4 == 0, "Only word-aligned structures are supported");

  if(numElements == 0)
  {
    outputArray = NULL;
    return true;
  }
  else
  {
    // Calculate size of array in bytes
    const unsigned int arrayBytes = sizeof(T) * numElements;
    const unsigned int arrayWords = arrayBytes / sizeof(uint32_t);
    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t%u bytes", arrayBytes);

    // Allocate output array
    outputArray = (T*)spin1_malloc(arrayBytes);
    if(outputArray == NULL)
    {
      return false;
    }

    // Copy data into newly allocated array
    spin1_memcpy(outputArray, inputPointer, arrayBytes);

    // Advance pointer
    inputPointer += arrayWords;
    return true;
  }
}
}
}
