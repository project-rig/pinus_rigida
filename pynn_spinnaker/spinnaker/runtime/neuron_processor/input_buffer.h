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
template<typename T>
class InputBufferBase
{
public:
  InputBufferBase() : m_InputBuffers(NULL), m_NumInputBuffers(0), m_DMABuffer(NULL)
  {
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  bool ReadSDRAMData(uint32_t *region, uint32_t, unsigned int numNeurons)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "InputBufferBase::ReadSDRAMData");

    // Read base address and num lookup entries from 1st 2 words
    m_NumInputBuffers = *region++;
    LOG_PRINT(LOG_LEVEL_INFO, "\tNum input buffers:%u", m_NumInputBuffers);

    // Copy key lookup entries
    if(!AllocateCopyStructArray(m_NumInputBuffers, region, m_InputBuffers))
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate input buffer array");
      return false;
    }

    // Allocate DMA buffer
    m_DMABuffer = (T*)spin1_malloc(sizeof(T) * numNeurons);
    if(m_DMABuffer == NULL)
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate DMA buffer");
      return false;
    }

#if LOG_LEVEL <= LOG_LEVEL_INFO
    for(unsigned int i = 0; i < m_NumInputBuffers; i++)
    {
      const auto &inputBuffer = m_InputBuffers[i];
      LOG_PRINT(LOG_LEVEL_INFO, "\t\tEntry:%u, Buffers:{%08x, %08x}, Receptor type:%u, Left shift to S1615:%d",
        i, inputBuffer.m_Buffers[0], inputBuffer.m_Buffers[1], inputBuffer.m_ReceptorType, inputBuffer.m_LeftShiftToS1615);
    }
#endif
    return true;
  }

  bool Fetch(unsigned int inputBufferIndex, uint tick, unsigned int numNeurons, uint tag)
  {
    // If there are input buffers outstanding
    if(inputBufferIndex < m_NumInputBuffers)
    {
      LOG_PRINT(LOG_LEVEL_TRACE, "\tStarting DMA of input buffer index:%u (%u)",
                inputBufferIndex, (tick + 1) % 2);

      // Start DMA into input buffer
      auto inputBuffer = m_InputBuffers[inputBufferIndex];
      spin1_dma_transfer(tag, const_cast<T*>(inputBuffer.m_Buffers[(tick + 1) % 2]),
                         m_DMABuffer, DMA_READ, numNeurons * sizeof(T));
      return false;
    }
    // Otherwise, all inputs are gathered - update neurons
    else
    {
      LOG_PRINT(LOG_LEVEL_TRACE, "\tAll input buffers processed, updating neurons");
      return true;
    }
  }

  template<typename G>
  void Process(unsigned int inputBufferIndex, unsigned int numNeurons,
                      G applyInputFunction)
  {
    // Get corresponding input buffer
    auto inputBuffer = m_InputBuffers[inputBufferIndex];

    LOG_PRINT(LOG_LEVEL_TRACE, "\tApplying input buffer:%u to receptor:%u with left shift:%d",
      inputBufferIndex, inputBuffer.m_ReceptorType, inputBuffer.m_LeftShiftToS1615);

    // If input buffer needs to be right-shifted to S1615
    const T *dmaEntry = m_DMABuffer;
    if(inputBuffer.m_LeftShiftToS1615 < 0)
    {
      // Loop through neurons, right shift and apply input
      auto rightShift = (const unsigned int)(-inputBuffer.m_LeftShiftToS1615);
      for(unsigned int n = 0; n < numNeurons; n++)
      {
        T input = *dmaEntry++;
        S1615 scaledInput = (S1615)(input >> rightShift);
#if LOG_LEVEL <= LOG_LEVEL_TRACE
        io_printf(IO_BUF, "%u (%knA),", input, scaledInput);
#endif
        applyInputFunction(n, scaledInput, inputBuffer.m_ReceptorType);
      }
    }
    // If input buffer needs to be left-shifted to S1615
    else
    {
      // Loop through neurons, left shift and apply input
      auto leftShift = (const unsigned int)inputBuffer.m_LeftShiftToS1615;
      for(unsigned int n = 0; n < numNeurons; n++)
      {
        T input = *dmaEntry++;
        S1615 scaledInput = (S1615)(input << leftShift);
#if LOG_LEVEL <= LOG_LEVEL_TRACE
        io_printf(IO_BUF, "%u (%knA),", input, scaledInput);
#endif
        applyInputFunction(n, scaledInput, inputBuffer.m_ReceptorType);
      }
    }

#if LOG_LEVEL <= LOG_LEVEL_TRACE
    io_printf(IO_BUF, "\n");
#endif
  }

private:
  //-----------------------------------------------------------------------------
  // Buffer
  //-----------------------------------------------------------------------------
  struct Buffer
  {
    const T *m_Buffers[2];
    uint32_t m_ReceptorType;
    int32_t m_LeftShiftToS1615;
  };

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  Buffer *m_InputBuffers;
  unsigned int m_NumInputBuffers;

  T *m_DMABuffer;
};
}