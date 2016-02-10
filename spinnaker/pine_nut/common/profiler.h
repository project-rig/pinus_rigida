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

#ifdef PROFILER_ENABLED
  static void WriteEntry(uint32_t tag)
  {
    if(s_SamplesRemaining > 0)
    {
      *s_Output++ = tc[T2_COUNT];
      *s_Output++ = tag;
      s_SamplesRemaining--;
    }
  }

  static void WriteEntryDisableFIQ(uint32_t tag)
  {
    DisableFIQ f;
    WriteEntry(tag);
  }

  static void WriteEntryDisableIRQFIQ(uint32_t tag)
  {
    DisableIRQFIQ f;
    WriteEntry(tag);
  }
#else
  static void WriteEntry(uint32_t){}
  static void WriteEntryDisableFIQ(uint32_t){}
  static void WriteEntryDisableIRQFIQ(uint32_t){}
#endif  // PROFILER_ENABLED

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

    Tag(Tag const &) = delete;
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

    TagDisableFIQ(TagDisableFIQ const &) = delete;
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

    TagDisableIRQFIQ(TagDisableIRQFIQ const &) = delete;
  };


private:
  //---------------------------------------
  // Members
  //---------------------------------------
#ifdef PROFILER_ENABLED
  static uint32_t *s_Count;
  static uint32_t s_SamplesRemaining;
  static uint32_t *s_Output;
#endif  // PROFILER_ENABLED
};
}
