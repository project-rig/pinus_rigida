#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../common/arm_intrinsics.h"
#include "../common/log.h"
#include "../common/utils.h"

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
  bool LookupRow(uint32_t key, const uint32_t *baseAddress, G getRowWordsFunction,
                 unsigned int &rowWords, const uint32_t *&rowAddress) const
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
        // **NOTE** add one as 0 is not a valid number
        const unsigned int rowSynapses = GetNumSynapses(lookupEntry.m_WordOffsetRowSynapses);
        const unsigned int wordOffset = GetWordOffset(lookupEntry.m_WordOffsetRowSynapses);
        
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

    LOG_PRINT(LOG_LEVEL_WARN, "Population associated with spike key %08x not found in key lookup", key);
    return false;
  }

  bool ReadSDRAMData(uint32_t *region, uint32_t)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "ReadKeyLookupRegion");

    // Read base address and num lookup entries from 1st 2 words
    m_NumLookupEntries = *region++;
    LOG_PRINT(LOG_LEVEL_INFO, "\tNum lookup entries:%u", m_NumLookupEntries);

    // Copy key lookup entries
    if(!AllocateCopyStructArray(m_NumLookupEntries, region, m_LookupEntries))
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate key lookup array");
      return false;
    }

#if LOG_LEVEL <= LOG_LEVEL_INFO
  for(unsigned int i = 0; i < m_NumLookupEntries; i++)
  {
    const auto &lookupEntry = m_LookupEntries[i];
    LOG_PRINT(LOG_LEVEL_INFO, "\t\tEntry:%u, Key:%08x, Mask:%08x, Num synapses:%u, Word offset:%u",
      i, lookupEntry.m_Key, lookupEntry.m_Mask,
      GetNumSynapses(lookupEntry.m_WordOffsetRowSynapses),
      GetWordOffset(lookupEntry.m_WordOffsetRowSynapses));
  }
#endif

    return true;
  }

private:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const uint32_t RowSynapsesMask = (1 << S) - 1;

  //-----------------------------------------------------------------------------
  // Static methods
  //-----------------------------------------------------------------------------
  static uint32_t GetNumSynapses(uint32_t word)
  {
    return (word & RowSynapsesMask) + 1;
  }

  static uint32_t GetWordOffset(uint32_t word)
  {
    return (word >> S);
  }

  //-----------------------------------------------------------------------------
  // KeyLookupEntry
  //-----------------------------------------------------------------------------
  // **THINK** mask could be a byte index into an array of
  // masks as there are going to be very few mask formats
  struct KeyLookupEntry
  {
    uint32_t m_Key;
    uint32_t m_Mask;
    uint32_t m_WordOffsetRowSynapses;
  };

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  KeyLookupEntry *m_LookupEntries;
  unsigned int m_NumLookupEntries;
};
}