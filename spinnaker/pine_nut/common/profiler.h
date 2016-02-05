#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "disable_interrupts.h"
#include "spinnaker.h"

//-----------------------------------------------------------------------------
// Common::Profiler
//-----------------------------------------------------------------------------
namespace Common
{
class Profiler
{
public:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const uint32_t Enter = (1 << 31);
  static const uint32_t Exit = 0;

  //-----------------------------------------------------------------------------
  // Public static API
  //-----------------------------------------------------------------------------
  static bool ReadSDRAMData(uint32_t *region, uint32_t);

  // Finalises profiling - potentially slow process of writing profiler_count to SDRAM
  static void Finalise();

  //-----------------------------------------------------------------------------
  // Tag
  //-----------------------------------------------------------------------------
  template<uint32_t T>
  class Tag
  {
  public:
    Tag()
    {
      Profiler::WriteEntry(Enter | T);
    }

    ~Tag()
    {
      Profiler::WriteEntry(Exit | T);
    }
  };

  //-----------------------------------------------------------------------------
  // TagDisableFIQ
  //-----------------------------------------------------------------------------
  template<uint32_t T>
  class TagDisableFIQ
  {
  public:
    TagDisableFIQ()
    {
      Profiler::WriteEntryDisableFIQ(Enter | T);
    }

    ~TagDisableFIQ()
    {
      Profiler::WriteEntryDisableFIQ(Exit | T);
    }
  };

  //-----------------------------------------------------------------------------
  // TagDisableIRQFIQ
  //-----------------------------------------------------------------------------
  template<uint32_t T>
  class TagDisableIRQFIQ
  {
  public:
    TagDisableIRQFIQ()
    {
      Profiler::WriteEntryDisableIRQFIQ(Enter | T);
    }

    ~TagDisableIRQFIQ()
    {
      Profiler::WriteEntryDisableIRQFIQ(Exit | T);
    }
  };


private:
  //-----------------------------------------------------------------------------
  // Private API
  //-----------------------------------------------------------------------------
  static void WriteEntry(uint32_t tag)
  {
#ifdef PROFILER_ENABLED
    if(s_ProfilerSamplesRemaining > 0)
    {
      *s_ProfilerOutput++ = tc[T2_COUNT];
      *s_ProfilerOutput++ = tag;
      s_ProfilerSamplesRemaining--;
    }
#endif  // PROFILER_ENABLED
  }

  static void WriteEntryDisableFIQ(uint32_t tag)
  {
#ifdef PROFILER_ENABLED
    DisableFIQ f;
    WriteEntry(tag);
#endif  // PROFILER_ENABLED
  }

  static void WriteEntryDisableIRQFIQ(uint32_t tag)
  {
#ifdef PROFILER_ENABLED
    DisableIRQ i;
    DisableFIQ f;
    WriteEntry(tag);
#endif  // PROFILER_ENABLED
  }

  //---------------------------------------
  // Members
  //---------------------------------------
#ifdef PROFILER_ENABLED
  static uint32_t *s_ProfilerCount;
  static uint32_t s_ProfilerSamplesRemaining;
  static uint32_t *s_ProfilerOutput;
#endif  // PROFILER_ENABLED
};
}
