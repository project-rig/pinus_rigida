#include "profiler.h"

// Common includes
#include "log.h"

//-----------------------------------------------------------------------------
// Common::Profiler
//-----------------------------------------------------------------------------
namespace Common
{
#ifdef PROFILER_ENABLED
uint32_t *Profiler::s_Count = NULL;
uint32_t Profiler::s_SamplesRemaining = 0;
uint32_t *Profiler::s_Output = NULL;
#endif  // PROFILER_ENABLED
//---------------------------------------
bool Profiler::ReadSDRAMData(uint32_t *region, uint32_t)
{
#ifdef PROFILER_ENABLED
  LOG_PRINT(LOG_LEVEL_INFO, "Profiler::ReadSDRAMData");

  // Read number of samples region can store from 1st word
  s_SamplesRemaining = region[0];

  LOG_PRINT(LOG_LEVEL_INFO, "\tNumber of profiler samples:%u",
            s_SamplesRemaining);

  // Cache pointers to SDRAM for writing data
  s_Count = &region[1];
  s_Output = &region[2];

  // If profiler is turned on, start timer 2 with no clock divider
  if(s_SamplesRemaining > 0)
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
  uint32_t wordsWritten = (s_Output - s_Count) - 1;
  *s_Count = wordsWritten;

  LOG_PRINT(LOG_LEVEL_INFO, "Profiler wrote %u bytes to %08x",
      (wordsWritten * 4) + 4, s_Count);
#endif  // PROFILER_ENABLED
}
}