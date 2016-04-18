#pragma once

// Standard includes
#include <algorithm>
#include <climits>
#include <cstdint>

// Common includes
#include "log.h"
#include "spinnaker.h"

// Namespaces
using namespace Common;

//-----------------------------------------------------------------------------
// Common::Flush
//-----------------------------------------------------------------------------
namespace Common
{
class Flush
{
public:
  Flush() : m_TimeSinceLastSpike(NULL), m_FlushTime(0)
  {
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  bool ReadSDRAMData(uint32_t *region, uint32_t, unsigned int numNeurons)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "Flush::ReadSDRAMData");

    // Read flush time from first word of region
    m_FlushTime = *region++;
    LOG_PRINT(LOG_LEVEL_INFO, "\tFlush time:%u timesteps", m_FlushTime);

     // If a flush time is set
    if(m_FlushTime != UINT32_MAX)
    {
      // Allocate array to hold time since last spike
      g_TimeSinceLastSpike = spin1_malloc(sizeof(uint16_t) * numNeurons);
      if(g_TimeSinceLastSpike == NULL)
      {
        LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate time since last spike array");
        return false;
      }

      // Initially zero all counts
      std::fill_n(g_TimeSinceLastSpike, g_AppWords[AppWordNumNeurons], 0);
    }
    return true;
  }

  bool ShouldFlush(unsigned int neuron, bool spiked)
  {
    if(m_TimeSinceLastSpike != NULL)
    {
      // If neuron's spiked, reset time since last spike
      if(spiked)
      {
        m_TimeSinceLastSpike[n] = 0;
      }
      // Otherwise
      else
      {
        // Increment time since last spike
        m_TimeSinceLastSpike[n]++;

        // If flush time has elapsed, clear timer and return true
        if(m_TimeSinceLastSpike[n] > m_FlushTime)
        {
          m_TimeSinceLastSpike[n] = 0;
          return true;
        }
      }
    }

    return false;
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint16_t *m_TimeSinceLastSpike = NULL;
  uint32_t m_FlushTime;
};
} // Common