#include "current_input_poisson.h"

// Common includes
#include "../common/config.h"
#include "../common/random/mars_kiss64.h"
#include "../common/log.h"
#include "../common/poisson_source.h"
#include "../common/profiler.h"
#include "../common/spike_recording.h"
#include "../common/spinnaker.h"

// Namespaces
using namespace Common::Random;
using namespace Common;
using namespace Common::Utils;
using namespace CurrentInputPoisson;

//-----------------------------------------------------------------------------
// Anonymous namespace
//-----------------------------------------------------------------------------
namespace
{
//----------------------------------------------------------------------------
// Enumerations
//----------------------------------------------------------------------------
enum DMATag
{
  DMATagOutputWrite,
};

//----------------------------------------------------------------------------
// Module level variables
//----------------------------------------------------------------------------
Common::Config g_Config;
uint32_t *g_OutputBuffers[2] = {NULL, NULL};

uint32_t *g_OutputWeights = NULL;

uint32_t *g_OutputBuffer = NULL;

const uint32_t *g_SynapticMatrixBaseAddress = NULL;

uint g_Tick = 0;

uint32_t g_AppWords[AppWordMax];

SpikeRecording g_SpikeRecording;

PoissonSource<MarsKiss64> g_PoissonSource;

//-----------------------------------------------------------------------------
bool ReadOutputBufferRegion(uint32_t *region, uint32_t)
{
  // Copy two output buffer pointers from region
  spin1_memcpy(g_OutputBuffers, region, 2 * sizeof(uint32_t*));

#if LOG_LEVEL <= LOG_LEVEL_INFO
  LOG_PRINT(LOG_LEVEL_INFO, "ReadOutputBufferRegion");
  for (uint32_t i = 0; i < 2; i++)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "\tIndex:%u, Address:%08x", i, g_OutputBuffers[i]);
  }
#endif

  return true;
}
//-----------------------------------------------------------------------------
bool ReadOutputWeightRegion(uint32_t *region, uint32_t)
{
  // Allocate and copy array of output weights from region
  if(!AllocateCopyStructArray(g_AppWords[AppWordNumCurrentSources], region, g_OutputWeights))
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate output weight array");
    return false;
  }

  // Allocate output buffer
  g_OutputBuffer = (uint32_t*)spin1_malloc(
    sizeof(uint32_t) * g_AppWords[AppWordNumCurrentSources]);
  if(g_OutputBuffer == NULL)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate output buffer array");
    return false;
  }

  return true;
}
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
    LOG_PRINT(LOG_LEVEL_INFO, "\tnum current sources=%u",
      g_AppWords[AppWordNumCurrentSources]);
  }

  // Read poisson source region
  if(!g_PoissonSource.ReadSDRAMData(
    Common::Config::GetRegionStart(baseAddress, RegionPoissonSource), flags))
  {
    return false;
  }

  // Read output buffer region
  if(!ReadOutputBufferRegion(
    Common::Config::GetRegionStart(baseAddress, RegionOutputBuffer),
    flags))
  {
    return false;
  }

  // Read output weight region
  if(!ReadOutputWeightRegion(
    Common::Config::GetRegionStart(baseAddress, RegionOutputWeight),
    flags))
  {
    return false;
  }

  // Read spike recording region
  if(!g_SpikeRecording.ReadSDRAMData(
    Common::Config::GetRegionStart(baseAddress, RegionSpikeRecording), flags,
    g_AppWords[AppWordNumCurrentSources]))
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
void TimerTick(uint tick, uint)
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

    // Zero output buffer
    for(unsigned int o = 0; o < g_AppWords[AppWordNumCurrentSources]; o++)
    {
      g_OutputBuffer[o] = 0;
    }

    // Create lambda function to add weight to output buffer
    auto emitSpikeLambda =
      [](unsigned int n)
      {
        g_OutputBuffer[n] += g_OutputWeights[n];
      };

    // Update poisson source
    g_PoissonSource.Update(tick, emitSpikeLambda, g_SpikeRecording);

    // Transfer spike recording buffer to SDRAM
    g_SpikeRecording.TransferBuffer();


#if LOG_LEVEL <= LOG_LEVEL_TRACE
    for(unsigned int i = 0; i < g_AppWords[AppWordNumCurrentSources]; i++)
    {
      io_printf(IO_BUF, "%u,", outputBuffer[i]);
    }
    io_printf(IO_BUF, "\n");
#endif

    // DMA output buffer into correct output buffer for this timer tick
    spin1_dma_transfer(DMATagOutputWrite, g_OutputBuffers[tick % 2],
                      g_OutputBuffer, DMA_WRITE,
                      g_AppWords[AppWordNumCurrentSources] * sizeof(uint32_t));
  }
}
} // anonymous namespace

//-----------------------------------------------------------------------------
// Entry point
//-----------------------------------------------------------------------------
extern "C" void c_main()
{
  //static_init();
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
  spin1_callback_on(TIMER_TICK,         TimerTick,         2);

  // Start simulation
  spin1_start(SYNC_WAIT);
}