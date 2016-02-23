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
//-----------------------------------------------------------------------------
// **TODO** const somewhere on inputPointer!
template<typename T>
bool AllocateCopyIndexedStructArray(unsigned int numElements, uint32_t *&inputPointer,
                                    uint16_t *&outputIndexArray, T *&outputArray)
{
  // Read the number of unique elements from first input word
  unsigned int numUniqueElements = (unsigned int)*inputPointer++;
  LOG_PRINT(LOG_LEVEL_TRACE, "\t\t%u unique elements", numUniqueElements);

  // If there are no elements, null both output arrays and returnt true
  if(numElements == 0)
  {
    outputIndexArray = NULL;
    outputArray = NULL;
    return true;
  }
  //  Otherwise
  else
  {
    // Calculate size of index array in bytes and words
    // (rounding up to keep word aligned)
    const unsigned int indexArrayBytes = sizeof(uint16_t) * numElements;
    const unsigned int indexArrayWords = (numElements / 2)
      + (((numElements & 1) != 0) ? 1 : 0);

    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t%u index bytes", indexArrayBytes);

    // Allocate output index array
    outputIndexArray = (uint16_t*)spin1_malloc(indexArrayBytes);
    if(outputIndexArray == NULL)
    {
      return false;
    }

    // Copy data into newly allocated array
    spin1_memcpy(outputIndexArray, inputPointer, indexArrayBytes);

    // Advance pointer
    inputPointer += indexArrayWords;

    // Use standard allocate copy function to copy unique elements into output array
    return AllocateCopyStructArray(numUniqueElements, inputPointer, outputArray);
  }
}
}
}
