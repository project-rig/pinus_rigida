#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../common/bit_field.h"
#include "../common/log.h"
#include "../common/spinnaker.h"

// Namespaces
using namespace Common;

//-----------------------------------------------------------------------------
// SynapseProcessor::SDRAMBackPropagation
//-----------------------------------------------------------------------------
namespace SynapseProcessor
{
class SDRAMBackPropagation
{
public:
  SDRAMBackPropagation()
  {
  }

  //--------------------------------------------------------------------------
  // Public API
  //--------------------------------------------------------------------------
  void Fetch(unsigned int tick, uint tag) const
  {
    // Start DMA of bitfield into local memory
    spin1_dma_transfer(tag, m_SDRAMBuffers[tick % 2], m_SpikeBitField,
                       DMA_READ, NumBitFieldBytes);
  }

  template<typename F>
  void Process(uint32_t numPostNeurons, F processSpikeFunction) const
  {
    BitField::ForEach(m_SpikeBitField, numPostNeurons, processSpikeFunction);
  }

  bool ReadSDRAMData(uint32_t *region, uint32_t)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "SDRAMBackPropagation::ReadSDRAMData");

    // Copy two SDRAM buffer pointers from region
    spin1_memcpy(m_SDRAMBuffers, region, 2 * sizeof(uint32_t*));

#if LOG_LEVEL <= LOG_LEVEL_INFO
    for (uint32_t i = 0; i < 2; i++)
    {
      LOG_PRINT(LOG_LEVEL_INFO, "\tBuffer:%08x", m_SDRAMBuffers[i]);
    }
#endif

    return true;
  }

private:
  //--------------------------------------------------------------------------
  // Constants
  //--------------------------------------------------------------------------
  static const unsigned int MaxNeurons = 512;
  static const unsigned int NumBitFieldBytes = (MaxNeurons / 8) + (((MaxNeurons % 8) == 0) ? 0 : 1);
  static const unsigned int NumBitFieldWords = (MaxNeurons / 32) + (((MaxNeurons % 32) == 0) ? 0 : 1);

  //--------------------------------------------------------------------------
  // Members
  //--------------------------------------------------------------------------
  // Bit-field of spikes from last timestep
  uint32_t m_SpikeBitField[NumBitFieldWords];

  // Addresses of SDRAM buffers
  uint32_t *m_SDRAMBuffers[2];
};
}