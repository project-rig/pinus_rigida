#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "log.h"

//-----------------------------------------------------------------------------
// Common::Profiler
//-----------------------------------------------------------------------------
namespace Common
{
template<unsigned int N>
class Statistics
{
public:
  Statistics() : m_SDRAMBaseAddress(NULL)
  {
    for(unsigned int i = 0; i < N; i++)
    {
      m_Statistics[i] = 0;
    }
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  bool ReadSDRAMData(uint32_t *region, uint32_t)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "Statistics::Statistics");

    // Cache pointer to region as base address for synaptic matrices
    m_SDRAMBaseAddress = region;

    LOG_PRINT(LOG_LEVEL_INFO, "\tStatistics base address:%08x",
              m_SDRAMBaseAddress);

    return true;
  }

  // Finalises profiling - potentially slow process of writing profiler_count to SDRAM
  void Finalise()
  {
    uint32_t *statistics = m_SDRAMBaseAddress;
    for(unsigned int i = 0; i < N; i++)
    {
      *statistics++ = m_Statistics[i];
    }
  }

  //-----------------------------------------------------------------------------
  // Operators
  //-----------------------------------------------------------------------------
  uint32_t& operator[](unsigned int i)
  {
    return m_Statistics[i];
  };

private:
  //---------------------------------------
  // Members
  //---------------------------------------
  uint32_t m_Statistics[N];
  uint32_t *m_SDRAMBaseAddress;
};
}