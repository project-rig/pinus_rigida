#include "profiler.h"

// Common includes
#include "log.h"

//-----------------------------------------------------------------------------
// Common::Profiler
//-----------------------------------------------------------------------------
namespace Common
{
#ifdef PROFILER_ENABLED
uint32_t *Profiler::s_ProfilerCount = NULL;
uint32_t Profiler::s_ProfilerSamplesRemaining = 0;
uint32_t *Profiler::s_ProfilerOutput = NULL;
#endif  // PROFILER_ENABLED
//---------------------------------------
bool Profiler::ReadSDRAMData(uint32_t *region, uint32_t)
{
#ifdef PROFILER_ENABLED
  // Read number of samples region can store from 1st word
  s_ProfilerSamplesRemaining = region[0];

  // Cache pointers to SDRAM for writing data
  s_ProfilerCount = &region[1];
  s_ProfilerOutput = &region[2];

  // If profiler is turned on, start timer 2 with no clock divider
  if(s_ProfilerSamplesRemaining > 0)
  {
    tc[T2_CONTROL] = 0x82;
    tc[T2_LOAD] = 0;
  }
#endif  // PROFILER_ENABLED

  return true;
}
//---------------------------------------
void Profiler::Finalise()
{
#ifdef PROFILER_ENABLED
  uint32_t wordsWritten = (s_ProfilerOutput - s_ProfilerCount) - 1;
  *s_ProfilerCount = wordsWritten;

  LOG_PRINT(LOG_LEVEL_INFO, "Profiler wrote %u bytes to %08x",
      (wordsWritten * 4) + 4, s_ProfilerCount);
#endif  // PROFILER_ENABLED
}
}