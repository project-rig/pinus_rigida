#include "delay_buffer.h"

// Common includes
#include "../common/log.h"

//-----------------------------------------------------------------------------
// SynapseProcessor::DelayBuffer
//-----------------------------------------------------------------------------
namespace SynapseProcessor
{
bool DelayBuffer::ReadSDRAMData(uint32_t *region, uint32_t)
{
  LOG_PRINT(LOG_LEVEL_INFO, "DelayBuffer::ReadSDRAMData");

  // Read number of delay slots and use to calculate mask
  const unsigned int numDelaySlots = (unsigned int)region[0];
  m_BufferSize = (unsigned int)region[1];
  m_DelayMask = numDelaySlots - 1;
  LOG_PRINT(LOG_LEVEL_INFO, "\tNum delay slots:%u, Delay mask:%x, Buffer size:%u",
            numDelaySlots, m_DelayMask, m_BufferSize);

  // Allocate SDRAM delay buffer pointers
  m_SDRAMDelayBuffers = (uint32_t***)spin1_malloc(sizeof(uint32_t**) * numDelaySlots);
  if(m_SDRAMDelayBuffers == NULL)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate pointers to SDRAM delay buffer");
    return false;
  }

  // Allocate delay buffer counts
  m_DelayBufferCount = (uint8_t*)spin1_malloc(sizeof(uint8_t) * numDelaySlots);
  if(m_DelayBufferCount == NULL)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate delay buffer counters");
    return false;
  }

  // Loop through delay slots
  for(unsigned int d = 0; d < numDelaySlots; d++)
  {
    // Allocate a delay buffer in SDRAM large enough to hold B pointers
    m_SDRAMDelayBuffers[d] = (uint32_t**)sark_xalloc(
      sv->sdram_heap, m_BufferSize * sizeof(uint32_t*), 0, ALLOC_LOCK);
    if(m_SDRAMDelayBuffers[d] == NULL)
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate SDRAM delay buffer");
      return false;
    }

    // Zero entry counter
    m_DelayBufferCount[d] = 0;
  }

  return true;
}
} // namespace DelayBuffer