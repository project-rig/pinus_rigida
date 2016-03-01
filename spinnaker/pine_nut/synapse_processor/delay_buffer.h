#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../common/spinnaker.h"

//-----------------------------------------------------------------------------
// SynapseProcessor::DelayBuffer
//-----------------------------------------------------------------------------
namespace SynapseProcessor
{
class DelayBuffer
{
public:
  DelayBuffer() : m_DelayMask(0), m_BufferSize(0), m_SDRAMDelayBuffers(NULL), m_DelayBufferCount(NULL)
  {
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  bool ReadSDRAMData(uint32_t *region, uint32_t);

  bool AddRow(unsigned int tick, uint32_t *row)
  {
    // Calculate index of buffer to use
    const unsigned int d = tick & m_DelayMask;

    // If there is space in this delay buffer, add row
    // pointer to SDRAM delay buffer and increment counter
    if(m_DelayBufferCount[d] < m_BufferSize)
    {
      m_SDRAMDelayBuffers[d][m_DelayBufferCount[d]++] = row;
      return true;
    }
    // Otherwise
    else
    {
      return false;
    }
  }

  uint32_t **GetDelayBuffer(unsigned int tick) const
  {
    return m_SDRAMDelayBuffers[tick & m_DelayMask];
  }

  unsigned int GetDelayBufferCount(unsigned int tick) const
  {
    return (unsigned int)m_DelayBufferCount[tick & m_DelayMask];
  }

  void ClearDelayBuffer(unsigned int tick)
  {
    // Reset count for this delay slot
    m_DelayBufferCount[tick & m_DelayMask] = 0;
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  // Mask to apply to ticks to get delay buffer index
  unsigned int m_DelayMask;

  // How big is each delay buffer
  unsigned int m_BufferSize;

  // Pointers to heads of delay buffers for each slot
  uint32_t ***m_SDRAMDelayBuffers;

  // Number of entries present in each delay buffer
  uint8_t *m_DelayBufferCount;
};
} // SynapseProcessor