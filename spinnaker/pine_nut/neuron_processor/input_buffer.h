#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../common/fixed_point_number.h"
#include "../common/log.h"
#include "../common/utils.h"

// Namespaces
using namespace Common::FixedPointNumber;
using namespace Common::Utils;

//-----------------------------------------------------------------------------
// NeuronProcessor::InputBuffers
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
class InputBuffer
{
public:
  InputBuffer() : m_InputBuffers(NULL), m_NumInputBuffers(0)
  {
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  bool ReadSDRAMData(const uint32_t *baseAddress, uint32_t)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "ReadInputBufferRegion");

    // Read base address and num lookup entries from 1st 2 words
    m_NumInputBuffers = baseAddress[0];
    LOG_PRINT(LOG_LEVEL_INFO, "\tNum input buffers:%u", m_NumInputBuffers);

    // Copy key lookup entries
    const uint32_t *structArray = &baseAddress[1];
    if(!AllocateCopyStructArray(m_NumInputBuffers, structArray, m_InputBuffers))
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate key lookup array");
      return false;
    }

#if LOG_LEVEL <= LOG_LEVEL_INFO
    for(unsigned int i = 0; i < m_NumInputBuffers; i++)
    {
      const auto &inputBuffer = m_InputBuffers[i];
      LOG_PRINT(LOG_LEVEL_INFO, "\t\tEntry:%u, Buffer:%08x, Receptor type:%u",
        i, inputBuffer.m_Buffer, inputBuffer.m_ReceptorType);
    }
#endif
    return true;
  }

private:
  //-----------------------------------------------------------------------------
  // Buffer
  //-----------------------------------------------------------------------------
  struct Buffer
  {
    const S1615 *m_Buffer;
    uint32_t m_ReceptorType;
  };

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  Buffer *m_InputBuffers;
  unsigned int m_NumInputBuffers;
};
}