#include "spike_source.h"

// Standard includes
#include <climits>

// Common includes
#include "../common/config.h"
#include "../common/log.h"
#include "../common/profiler.h"
#include "../common/spike_recording.h"
#include "../common/spinnaker.h"
#include "../common/utils.h"

// Configuration include
#include "config.h"

// Namespaces
using namespace Common;
using namespace SpikeSource;

//-----------------------------------------------------------------------------
// Anonymous namespace
//-----------------------------------------------------------------------------
namespace
{
//----------------------------------------------------------------------------
// Module level variables
//----------------------------------------------------------------------------
Common::Config g_Config;
uint32_t g_AppWords[AppWordMax];

SpikeRecording g_SpikeRecording;

Source g_SpikeSource;

//----------------------------------------------------------------------------
// Functions
//-----------------------------------------------------------------------------
bool ReadSDRAMData(uint32_t *baseAddress, uint32_t flags)
{
  // Verify data header
  if(!g_Config.VerifyHeader(baseAddress, flags))
  {
    return false;
  }

  // Read system region
  if(!g_Config.ReadSystemRegion(
    Common::Config::GetRegionStart(baseAddress, RegionSystem),
    flags, AppWordMax, g_AppWords))
  {
    return false;
  }
  else
  {
    LOG_PRINT(LOG_LEVEL_INFO, "\tkey=%08x, num spike sources=%u",
      g_AppWords[AppWordKey], g_AppWords[AppWordNumSpikeSources]);
  }

  // Read source region
  if(!g_SpikeSource.ReadSDRAMData(
    Common::Config::GetRegionStart(baseAddress, RegionSpikeSource), flags,
    g_AppWords[AppWordNumSpikeSources]))
  {
    return false;
  }

  // Read spike recording region
  if(!g_SpikeRecording.ReadSDRAMData(
    Common::Config::GetRegionStart(baseAddress, RegionSpikeRecording), flags,
    g_AppWords[AppWordNumSpikeSources]))
  {
    return false;
  }

  // Read profiler region
  if(!Common::Profiler::ReadSDRAMData(
    Common::Config::GetRegionStart(baseAddress, RegionProfiler),
    flags))
  {
    return false;
  }


  return true;
}

//-----------------------------------------------------------------------------
// Event handler functions
//-----------------------------------------------------------------------------
static void DMATransferDone(uint, uint tag)
{
  if(!g_SpikeSource.DMATransferDone(tag))
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Spike source unable to handle DMA tag %u", tag);
  }
}
//-----------------------------------------------------------------------------
static void TimerTick(uint tick, uint)
{
  // Subtract 1 from tick as they start at 1
  tick--;

  // If a fixed number of simulation ticks are specified and these have passed
  if(g_Config.GetSimulationTicks() != UINT32_MAX
    && tick >= g_Config.GetSimulationTicks())
  {
    LOG_PRINT(LOG_LEVEL_INFO, "Simulation complete");

    // Finalise profiling
    Common::Profiler::Finalise();

    // Finalise any recordings that are in progress, writing
    // back the final amounts of samples recorded to SDRAM
    //recording_finalise();
    spin1_exit(0);
  }
  // Otherwise
  else
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "Timer tick %u", tick);

    // Create lambda function to emit spike
    auto emitSpikeLambda =
      [](unsigned int n)
      {
        // Send spike
        uint32_t key = g_AppWords[AppWordKey] | n;
        while(!spin1_send_mc_packet(key, 0, NO_PAYLOAD))
        {
          spin1_delay_us(1);
        }
      };

    // Update spike source
    g_SpikeSource.Update(tick, emitSpikeLambda, g_SpikeRecording,
      g_AppWords[AppWordNumSpikeSources]
    );

    // Transfer spike recording buffer to SDRAM
    g_SpikeRecording.TransferBuffer();
  }
}
} // Anonymous namespace

//-----------------------------------------------------------------------------
// Entry point
//-----------------------------------------------------------------------------
extern "C" void c_main()
{
  // Get this core's base address using alloc tag
  uint32_t *baseAddress = Common::Config::GetBaseAddressAllocTag();
  
  // If reading SDRAM data fails
  if(!ReadSDRAMData(baseAddress, 0))
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Error reading SDRAM data");
    return;
  }
  
  // Set timer tick (in microseconds) in both timer and 
  spin1_set_timer_tick(g_Config.GetTimerPeriod());
  
  // Register callbacks
  spin1_callback_on(TIMER_TICK,         TimerTick,        2);
  spin1_callback_on(DMA_TRANSFER_DONE,  DMATransferDone,   0);
  
  // Start simulation
  spin1_start(SYNC_WAIT);
}