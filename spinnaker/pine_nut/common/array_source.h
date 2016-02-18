#pragma once

// Common includes
#include "bit_field.h"
#include "log.h"
#include "spinnaker.h"
#include "spike_recording.h"
#include "utils.h"

// Namespaces
using namespace Common;
using namespace Common::Utils;

//-----------------------------------------------------------------------------
// Common::ArraySource
//-----------------------------------------------------------------------------
namespace Common
{
class ArraySource
{
public:
  ArraySource() : m_NextSpikeTick(0), m_SpikeBlockSizeWords(0),
    m_NextSpikeBlockAddress(NULL), m_DMABuffer(NULL), m_State(StateInactive)
  {
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  bool ReadSDRAMData(uint32_t *region, uint32_t, unsigned int numNeurons);
  bool DMATransferDone(uint tag);

  template<typename E>
  void Update(uint tick, E emitSpikeFunction, SpikeRecording &spikeRecording,
              unsigned int numNeurons)
  {
    // If a spike block has been transferred ready for this tick
    if(m_NextSpikeTick == tick)
    {
      // If there is data in the buffer
      if(m_State == StateSpikeBlockInBuffer)
      {
        // Loop through sources
        for(unsigned int s = 0; s < numNeurons; s++)
        {
          // If this source has spiked
          bool spiked = BitField::TestBit(&m_DMABuffer[1], m_SpikeBlockSizeWords - 1);
          if(spiked)
          {
            // Emit a spike
            LOG_PRINT(LOG_LEVEL_TRACE, "\t\tEmitting spike");
            emitSpikeFunction(s);
          }

          // Record spike
          spikeRecording.RecordSpike(s, spiked);
        }

        // Update next spike tick from start of block and
        // Advance offset to next block to fetch
        m_NextSpikeTick = m_DMABuffer[0];
        m_NextSpikeBlockAddress += m_SpikeBlockSizeWords;

        // Set state to DMA progress and start DMA
        m_State = StateDMAInProgress;

        // Start a DMA transfer from the absolute address of the spike block into buffer
        spin1_dma_transfer(DMATagSpikeDataRead, const_cast<uint32_t*>(m_NextSpikeBlockAddress),
          m_DMABuffer, DMA_READ, m_SpikeBlockSizeWords * sizeof(uint32_t));
      }
      // Otherwise error
      else
      {
        LOG_PRINT(LOG_LEVEL_WARN, "DMA hasn't completed in time for next tick");
      }
    }
  }

private:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const uint DMATagSpikeDataRead = 0;

  //-----------------------------------------------------------------------------
  // Enumerations
  //-----------------------------------------------------------------------------
  enum State
  {
    StateInactive,
    StateDMAInProgress,
    StateSpikeBlockInBuffer,
  };

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint m_NextSpikeTick;
  unsigned int m_SpikeBlockSizeWords;
  const uint32_t *m_NextSpikeBlockAddress;
  uint32_t *m_DMABuffer;
  State m_State;
};
} // namespace Common