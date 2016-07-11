#include "supervisor_synapse_processor.h"

// Standard includes
#include <climits>

// Common includes
#include "../common/config.h"
#include "../common/log.h"
#include "../common/profiler.h"
#include "../common/sdram_back_propagation_output.h"
#include "../common/spinnaker.h"
#include "../common/statistics.h"

// Configuration include
#include "config.h"

// Namespaces
using namespace Common;
using namespace SupervisorSynapseProcessor;

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
  DMATagRowRead,
  DMATagBackPropagationWrite
};

//----------------------------------------------------------------------------
// DMABuffer
//----------------------------------------------------------------------------
typedef uint32_t DMABuffer[1024];

//----------------------------------------------------------------------------
// Module level variables
//----------------------------------------------------------------------------
Config g_Config;
KeyLookup g_KeyLookup;
SpikeInputBuffer g_SpikeInputBuffer;
Statistics<StatWordMax> g_Statistics;

SDRAMBackPropagationOutput g_BackPropagationOutput;

uint32_t g_AppWords[AppWordMax];

uint32_t *g_SynapticMatrixBaseAddress = NULL;

uint g_Tick = 0;

bool g_DMABusy = false;
DMABuffer g_DMABuffers[2];
unsigned int g_DMARowBufferIndex = 0;

//-----------------------------------------------------------------------------
// Module inline functions
//-----------------------------------------------------------------------------
inline void DMASwapRowBuffers()
{
  g_DMARowBufferIndex ^= 1;
}
//-----------------------------------------------------------------------------
inline DMABuffer &DMACurrentRowBuffer()
{
  return g_DMABuffers[g_DMARowBufferIndex];
}
//-----------------------------------------------------------------------------
inline DMABuffer &DMANextRowBuffer()
{
  return g_DMABuffers[g_DMARowBufferIndex ^ 1];
}
//-----------------------------------------------------------------------------
inline void DMAStartRowFetchPipeline()
{
  // If we're not already processing synaptic dmas,
  // flag pipeline as busy and trigger a user event
  if(!g_DMABusy)
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "Triggering user event for new spike");

    if(spin1_trigger_user_event(0, 0))
    {
      g_DMABusy = true;
    }
    else
    {
      LOG_PRINT(LOG_LEVEL_WARN, "Could not trigger user event");
    }
  }
}

//-----------------------------------------------------------------------------
// Module functions
//-----------------------------------------------------------------------------
bool ReadSynapticMatrixRegion(uint32_t *region, uint32_t)
{
  LOG_PRINT(LOG_LEVEL_INFO, "ReadSynapticMatrixRegion");

  // Cache pointer to region as base address for synaptic matrices
  g_SynapticMatrixBaseAddress = region;

  LOG_PRINT(LOG_LEVEL_INFO, "\tSynaptic matrix base address:%08x",
            g_SynapticMatrixBaseAddress);

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
    Config::GetRegionStart(baseAddress, RegionSystem),
    flags, AppWordMax, g_AppWords))
  {
    return false;
  }
  else
  {
    LOG_PRINT(LOG_LEVEL_INFO, "\tNum post-neurons:%u",
      g_AppWords[AppWordNumPostNeurons]);
  }

  // Read key lookup region
  if(!g_KeyLookup.ReadSDRAMData(
    Config::GetRegionStart(baseAddress, RegionKeyLookup),
    flags))
  {
    return false;
  }

  // Read synaptic matrix region
  if(!ReadSynapticMatrixRegion(
    Config::GetRegionStart(baseAddress, RegionSynapticMatrix),
    flags))
  {
    return false;
  }

  // Read profiler region
  if(!Profiler::ReadSDRAMData(
    Config::GetRegionStart(baseAddress, RegionProfiler),
    flags))
  {
    return false;
  }

  if(!g_Statistics.ReadSDRAMData(
    Config::GetRegionStart(baseAddress, RegionStatistics),
    flags))
  {
    return false;
  }

  // Read back propagation region
  if(!g_BackPropagationOutput.ReadSDRAMData(
    Config::GetRegionStart(baseAddress, RegionBackPropagationOutput), flags,
                           g_AppWords[AppWordNumPostNeurons]))
  {
    return false;
  }

  return true;
}
//-----------------------------------------------------------------------------
void SetupNextDMARowRead()
{
  Profiler::TagDisableFIQ<ProfilerTagSetupNextDMARowRead> p;

  // If there's another spike in the input buffer
  uint32_t key;
  if(g_SpikeInputBuffer.GetNextSpike(key))
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "Setting up DMA read for spike %x", key);

    // Create lambda function to convert number of synapses to a row length in words
    auto getRowWordsLambda =
      [](unsigned int rowSynapses)
      {
        const unsigned int indexBytes = rowSynapses * sizeof(uint16_t);
        return 1 + (indexBytes / 4) + (((indexBytes % 4) == 0) ? 0 : 1);
      };

    // Decode key to get address and length of destination synaptic row
    unsigned int rowWords;
    uint32_t *rowAddress;
    if(g_KeyLookup.LookupRow(key, g_SynapticMatrixBaseAddress, getRowWordsLambda,
      rowWords, rowAddress))
    {
      LOG_PRINT(LOG_LEVEL_TRACE, "\tRow words:%u, Row address:%08x",
                rowWords, rowAddress);

      // Start a DMA transfer to fetch this synaptic row into next buffer
      g_Statistics[StatRowRequested]++;
      spin1_dma_transfer(DMATagRowRead, rowAddress, DMANextRowBuffer(),
                         DMA_READ, rowWords * sizeof(uint32_t));

      // Flip DMA buffers and stop
      DMASwapRowBuffers();
      return;
    }
    else
    {
      LOG_PRINT(LOG_LEVEL_TRACE, "Population associated with spike key %08x not found in key lookup", key);
      g_Statistics[StatWordKeyLookupFail]++;
    }
  }

  // Stop pipeline
  g_DMABusy = false;
}

//-----------------------------------------------------------------------------
// Event handler functions
//-----------------------------------------------------------------------------
void MCPacketReceived(uint key, uint)
{
  Profiler::Tag<ProfilerTagMCPacketReceived> p;

  LOG_PRINT(LOG_LEVEL_TRACE, "Received spike %x at tick %u, DMA Busy = %u",
            key, g_Tick, g_DMABusy);

  // If there was space to add spike to incoming
  // spike queue, start DMA row fetch pipeline
  if(g_SpikeInputBuffer.AddSpike(key))
  {
    DMAStartRowFetchPipeline();
  }
  else
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "Cannot add spike to input buffer");
    g_Statistics[StatWordInputBufferOverflows]++;
  }

}
//-----------------------------------------------------------------------------
void DMATransferDone(uint, uint tag)
{
  if(tag == DMATagRowRead)
  {
    // Cache the current row buffer as starting
    // a new row read will potentially flip buffers
    auto &dmaCurrentRowBuffer = DMACurrentRowBuffer();

    // Setup next row read so, ideally, data will be
    // available as soon as processing of current row completes
    SetupNextDMARowRead();

    // Process the current row, using this function to apply
    Profiler::WriteEntryDisableFIQ(Profiler::Enter | ProfilerTagProcessRow);

    // Loop through words in new row
    register uint16_t *synapticWords = (uint16_t*)&dmaCurrentRowBuffer[1];
    register uint32_t count = dmaCurrentRowBuffer[0];
    for(; count > 0; count--)
    {
      g_BackPropagationOutput.RecordSpike((uint32_t)*synapticWords++);
    }

    Profiler::WriteEntryDisableFIQ(Profiler::Exit | ProfilerTagProcessRow);
  }
  else if(tag == DMATagBackPropagationWrite)
  {
    g_BackPropagationOutput.ClearBuffer();
  }
  else
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "DMA transfer done with unknown tag %u", tag);
  }
}
//-----------------------------------------------------------------------------
void UserEvent(uint, uint)
{
  // Setup next row read
  SetupNextDMARowRead();
}
//-----------------------------------------------------------------------------
void TimerTick(uint tick, uint)
{
  Profiler::TagDisableIRQFIQ<ProfilerTagTimerTick> p;

  // Cache tick
  // **NOTE** ticks start at 1
  g_Tick = (tick - 1);

  // If a fixed number of simulation ticks are specified and these have passed
  if(g_Config.GetSimulationTicks() != UINT32_MAX
    && g_Tick >= g_Config.GetSimulationTicks())
  {
    LOG_PRINT(LOG_LEVEL_INFO, "Simulation complete");

    // Finalise profiling
    Profiler::Finalise();

    // Finalise statistics
    g_Statistics.Finalise();

    // Exit simulation
    spin1_exit(0);
  }
  else
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "Timer tick %u", g_Tick);

    // Write back propagation to buffer
    g_BackPropagationOutput.TransferBuffer(g_Tick, DMATagBackPropagationWrite);
  }
}
} // anonymous namespace

//-----------------------------------------------------------------------------
// Entry point
//-----------------------------------------------------------------------------
extern "C" void c_main()
{
  // Get this core's base address using alloc tag
  uint32_t *baseAddress = Config::GetBaseAddressAllocTag();

  // If reading SDRAM data fails
  if(!ReadSDRAMData(baseAddress, 0))
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Error reading SDRAM data");
    return;
  }

  // Initialise
  g_DMABusy = false;
  g_DMARowBufferIndex = 0;

  // Set timer tick (in microseconds) in both timer and
  spin1_set_timer_tick(g_Config.GetTimerPeriod());

  // Register callbacks
  spin1_callback_on(MC_PACKET_RECEIVED, MCPacketReceived, -1);
  spin1_callback_on(DMA_TRANSFER_DONE,  DMATransferDone,   0);
  spin1_callback_on(USER_EVENT,         UserEvent,         0);
  spin1_callback_on(TIMER_TICK,         TimerTick,         2);

  // Start simulation
  spin1_start(SYNC_WAIT);
}