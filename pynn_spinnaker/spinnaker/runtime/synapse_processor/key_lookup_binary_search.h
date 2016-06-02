#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../common/arm_intrinsics.h"
#include "../common/log.h"
#include "../common/utils.h"

// Synapse processor includes
#include "row_offset_length.h"

// Namespaces
using namespace Common::ARMIntrinsics;
using namespace Common::Utils;

//-----------------------------------------------------------------------------
// SynapseProcessor::KeyLookupBinarySearch
//-----------------------------------------------------------------------------
namespace SynapseProcessor
{
template<unsigned int S>
class KeyLookupBinarySearch
{
public:
  KeyLookupBinarySearch() : m_LookupEntries(NULL), m_NumLookupEntries(0)
  {
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  template<typename G>
  bool LookupRow(uint32_t key, uint32_t *baseAddress, G getRowWordsFunction,
                 unsigned int &rowWords, uint32_t *&rowAddress) const
  {
    // Binary search lookup table
    unsigned int iMin = 0;
    unsigned int iMax = m_NumLookupEntries;
    while (iMin < iMax)
    {
      const unsigned int iMid = (iMax + iMin) / 2;
      const auto &lookupEntry = m_LookupEntries[iMid];
      if ((key & lookupEntry.m_Mask) == lookupEntry.m_Key)
      {
        // Extract number of synapses and word offset from lookup entry
        const unsigned int rowSynapses = lookupEntry.m_WordOffsetRowSynapses.GetNumSynapses();
        const unsigned int wordOffset = 2 * lookupEntry.m_WordOffsetRowSynapses.GetWordOffset();
        
        // Extract neuron ID from key
        // **NOTE** assumed to be at bottom of mask
        const unsigned int neuronID = key &  ~lookupEntry.m_Mask;
        
        // Convert number of synapses to number of words 
        rowWords = getRowWordsFunction(rowSynapses);
        
        // Add word offset to base address to get row address
        // **NOTE** neuronID < 1024 and row words < 1024 - __smalbb!
        rowAddress = baseAddress + (uint32_t)__smlabb(
          (int32_t)neuronID, (int32_t)rowWords, (int32_t)wordOffset);
        
        return true;
      }
      // Otherwise, entry must be in upper part of the table
      else if (lookupEntry.m_Key < key)
      {
        iMin = iMid + 1;
      }
      // Otherwise, entry must be in lower part of the table
      else
      {
        iMax = iMid;
      }
    }

    return false;
  }

  bool ReadSDRAMData(uint32_t *region, uint32_t)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "KeyLookupBinarySearch::ReadSDRAMData");

    // Read base address and num lookup entries from 1st 2 words
    m_NumLookupEntries = *region++;
    LOG_PRINT(LOG_LEVEL_INFO, "\tNum lookup entries:%u", m_NumLookupEntries);

    // Copy key lookup entries
    if(!AllocateCopyStructArray(m_NumLookupEntries, region, m_LookupEntries))
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate key lookup array");
      return false;
    }

#if LOG_LEVEL <= LOG_LEVEL_TRACE
  for(unsigned int i = 0; i < m_NumLookupEntries; i++)
  {
    const auto &lookupEntry = m_LookupEntries[i];
    LOG_PRINT(LOG_LEVEL_TRACE, "\t\tEntry:%u, Key:%08x, Mask:%08x, Num synapses:%u, Word offset:%u",
      i, lookupEntry.m_Key, lookupEntry.m_Mask,
      lookupEntry.m_WordOffsetRowSynapses.GetNumSynapses(),
      lookupEntry.m_WordOffsetRowSynapses.GetWordOffset());
  }
#endif

    return true;
  }

private:
  //-----------------------------------------------------------------------------
  // KeyLookupEntry
  //-----------------------------------------------------------------------------
  // **THINK** mask could be a byte index into an array of
  // masks as there are going to be very few mask formats
  struct KeyLookupEntry
  {
    uint32_t m_Key;
    uint32_t m_Mask;
    RowOffsetLength<S> m_WordOffsetRowSynapses;
  };

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  KeyLookupEntry *m_LookupEntries;
  unsigned int m_NumLookupEntries;
};
}