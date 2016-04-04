#include "synapse_processor.h"

// Common includes
#include "../common/config.h"
#include "../common/log.h"
#include "../common/profiler.h"
#include "../common/spinnaker.h"
#include "../common/statistics.h"

// Synapse processor includes
#include "spike_back_propagation.h"

// Configuration include
#include "config.h"

// Namespaces
using namespace Common;
using namespace SynapseProcessor;

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
  DMATagRowWrite,
  DMATagOutputWrite,
  DMATagDelayBufferRead,
};

//----------------------------------------------------------------------------
// DMABuffer
//----------------------------------------------------------------------------
struct DMABuffer
{
  // Address of row in SDRAM
  uint32_t *m_SDRAMAddress;

  // Is this spike a flush message
  // (used to force an plasticity update)
  bool m_Flush;

  // Data read from SDRAM
  uint32_t m_Data[SynapseType::MaxRowWords];
};

//----------------------------------------------------------------------------
// Module level variables
//----------------------------------------------------------------------------
Config g_Config;
RingBuffer g_RingBuffer;
DelayBuffer g_DelayBuffer;
KeyLookup g_KeyLookup;
SpikeInputBuffer g_SpikeInputBuffer;
Statistics<StatWordMax> g_Statistics;
SynapseType g_Synapse;
SpikeBackPropagation g_SpikeBackPropagation;

uint32_t g_AppWords[AppWordMax];

uint32_t *g_OutputBuffers[2] = {NULL, NULL};

uint32_t *g_SynapticMatrixBaseAddress = NULL;

uint g_CurrentDelayRowIndex = 0;
bool g_DelayRowBufferFetched = false;

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
    LOG_PRINT(LOG_LEVEL_INFO, "\tWeight fixed point:%u, Num post-neurons:%u",
      g_AppWords[AppWordWeightFixedPoint], g_AppWords[AppWordNumPostNeurons]);
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

   // Read plasticity region
  if(!g_Synapse.ReadSDRAMData(
    Config::GetRegionStart(baseAddress, RegionPlasticity),
    flags))
  {
    return false;
  }

  // Read output buffer region
  if(!ReadOutputBufferRegion(
    Config::GetRegionStart(baseAddress, RegionOutputBuffer),
    flags))
  {
    return false;
  }

  if(!g_DelayBuffer.ReadSDRAMData(
    Config::GetRegionStart(baseAddress, RegionDelayBuffer),
    flags))
  {
    return false;
  }

  if(!g_SpikeBackPropagation.ReadSDRAMData(
    Config::GetRegionStart(baseAddress, RegionSpikeBackPropagation),
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

  return true;
}
//-----------------------------------------------------------------------------
void SetupNextDMARowRead()
{
  Profiler::TagDisableFIQ<ProfilerTagSetupNextDMARowRead> p;

  // While there's the possibility that there might be a DMA we can start
  while(true)
  {
    // If there's another spike in the input buffer
    uint32_t key;
    if(g_SpikeInputBuffer.GetNextSpike(key))
    {
      // If this spike should be treated as back-propagation
      // input for the synapses, allow synapse model to process it
      unsigned int localNeuronIndex;
      if(g_SpikeBackPropagation.GetLocalNeuronIndex(key, localNeuronIndex))
      {
        g_Synapse.AddPostSynapticSpike(g_Tick, localNeuronIndex);
      }

      LOG_PRINT(LOG_LEVEL_TRACE, "Setting up DMA read for spike %x", key);

      // Create lambda function to convert number of synapses to a row length in words
      auto getRowWordsLambda =
        [](unsigned int rowSynapses)
        {
          return g_Synapse.GetRowWords(rowSynapses);
        };

      // Decode key to get address and length of destination synaptic row
      unsigned int rowWords;
      uint32_t *rowAddress;
      if(g_KeyLookup.LookupRow(key, g_SynapticMatrixBaseAddress, getRowWordsLambda,
        rowWords, rowAddress))
      {
        LOG_PRINT(LOG_LEVEL_TRACE, "\tRow words:%u, Row address:%08x",
                  rowWords, rowAddress);

        // Store SDRAM address of row in buffer
        // so it can be written back if required
        DMACurrentRowBuffer().m_SDRAMAddress = rowAddress;
        DMACurrentRowBuffer().m_Flush = false;

        // Start a DMA transfer to fetch this synaptic row into current buffer
        g_Statistics[StatRowRequested]++;
        spin1_dma_transfer(DMATagRowRead, rowAddress, DMACurrentRowBuffer().m_Data,
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
    // Otherwise, if a delay row buffer is present for this tick and all rows in it haven't been processed
    else if(g_DelayRowBufferFetched && g_CurrentDelayRowIndex < g_DelayBuffer.GetRowCount(g_Tick))
    {
      // Get next delay row from buffer
      auto delayRow = g_DelayBuffer.GetRow(g_CurrentDelayRowIndex++);

      // Convert number of synapses to words and get address from synaptic matrix base
      unsigned int delayRowWords = g_Synapse.GetRowWords(delayRow.GetNumSynapses());
      uint32_t *delayRowAddress = g_SynapticMatrixBaseAddress + delayRow.GetWordOffset();

      LOG_PRINT(LOG_LEVEL_TRACE, "Setting up DMA read for delay row index:%u, synapse:%u, words:%u, address:%08x",
                g_CurrentDelayRowIndex - 1, delayRow.GetNumSynapses(), delayRowWords, delayRowAddress);

      // Store SDRAM address of row in buffer
      // so it can be written back if required
      DMACurrentRowBuffer().m_SDRAMAddress = delayRowAddress;
      DMACurrentRowBuffer().m_Flush = false;

      // Start a DMA transfer to fetch this synaptic row into current buffer
      g_Statistics[StatDelayRowRequested]++;
      spin1_dma_transfer(DMATagRowRead, delayRowAddress, DMACurrentRowBuffer().m_Data,
                        DMA_READ, delayRowWords * sizeof(uint32_t));

      // Flip DMA buffers and stop
      DMASwapRowBuffers();
      return;
    }
    // Otherwise, there's nothing more to DMA
    // so flag the pipeline as idle and stop
    else
    {
      g_DMABusy = false;
      return;
    }
  }
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
    // Create lambda function to add a weight to the ring-buffer
    auto addWeightLambda = 
      [](unsigned int tick, unsigned int index, uint32_t weight) 
      {
        LOG_PRINT(LOG_LEVEL_TRACE, "\t\tAdding weight %u to neuron %u for tick %u",
                  weight, index, tick);
        g_RingBuffer.AddWeight(tick, index, weight);
      };

    // Create lambda function to add a delay extension to the delay buffer
    auto addDelayRowLambda =
      [](unsigned int tick, uint32_t word)
      {
        auto rowOffsetLength = DelayBuffer::R(word);
        LOG_PRINT(LOG_LEVEL_TRACE, "\t\tAdding delay extension row for tick %u, num synapses:%u, offset word:%u",
          tick, rowOffsetLength.GetNumSynapses(), rowOffsetLength.GetWordOffset());
        g_DelayBuffer.AddRow(tick, rowOffsetLength);
      };

    // Create lambda function to write back row
    auto writeBackRowLambda =
      [](uint32_t *sdramAddress, uint32_t *localAddress, unsigned int numWords)
      {
        LOG_PRINT(LOG_LEVEL_TRACE, "\t\tWriting back %u words to SDRAM address:%08x",
                  numWords, sdramAddress);
        spin1_dma_transfer(DMATagRowWrite, sdramAddress, localAddress,
                           DMA_WRITE, numWords * sizeof(uint32_t));
      };
    
    // Process the next row in the DMA buffer, using this function to apply
    Profiler::WriteEntryDisableFIQ(Profiler::Enter | ProfilerTagProcessRow);
    g_Synapse.ProcessRow(g_Tick, DMANextRowBuffer().m_Data, DMANextRowBuffer().m_SDRAMAddress, DMANextRowBuffer().m_Flush,
                         addWeightLambda, addDelayRowLambda, writeBackRowLambda);
    Profiler::WriteEntryDisableFIQ(Profiler::Exit | ProfilerTagProcessRow);

    // Setup next row read
    SetupNextDMARowRead();
  }
  else if(tag == DMATagOutputWrite)
  {
    // This timesteps output has been written from
    // the ring-buffer so we can now zero it
    g_RingBuffer.ClearOutputBuffer(g_Tick);

    // Fetch delay buffer for this timestep
    // **NOTE** this will only cause a DMA if the buffer has any entries
    g_DelayBuffer.Fetch(g_Tick, DMATagDelayBufferRead);
  }
  else if(tag == DMATagDelayBufferRead)
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "DMA read of delay buffer for tick %u complete", g_Tick);

    // Set flag to show that row buffer has been
    // fetched and start DMA row fetch pipeline
    g_DelayRowBufferFetched = true;
    DMAStartRowFetchPipeline();
  }
  else if(tag != DMATagRowWrite)
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

  // If all delay rows weren't processed last timer tick
  const unsigned int nonProcessedRows = g_DelayBuffer.GetRowCount(g_Tick) - g_CurrentDelayRowIndex;
  if(nonProcessedRows != 0)
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "%u delay rows were processed last timer tick",
              nonProcessedRows);
    g_Statistics[StatWordDelayBuffersNotProcessed] += nonProcessedRows;
  }

  // Clear the delay buffer for the last tick
  g_DelayBuffer.Clear(g_Tick);

  // Reset delay rows counter and fetched flag
  g_DelayRowBufferFetched = false;
  g_CurrentDelayRowIndex = 0;

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

    // Exit
    spin1_exit(0);
  }
  else
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "Timer tick %u, writing 'back' of ring-buffer to output buffer %u (%08x)",
              g_Tick, (g_Tick % 2), g_OutputBuffers[g_Tick % 2]);

    // Get output buffer from 'back' of ring-buffer
    const RingBuffer::Type *outputBuffer = g_RingBuffer.GetOutputBuffer(g_Tick);

#if LOG_LEVEL <= LOG_LEVEL_TRACE
    for(unsigned int i = 0; i < g_AppWords[AppWordNumPostNeurons]; i++)
    {
      io_printf(IO_BUF, "%u,", outputBuffer[i]);
    }
    io_printf(IO_BUF, "\n");
#endif

    // DMA output buffer into correct output buffer for this timer tick
    spin1_dma_transfer(DMATagOutputWrite, g_OutputBuffers[g_Tick % 2],
                      const_cast<RingBuffer::Type*>(outputBuffer), DMA_WRITE,
                      g_AppWords[AppWordNumPostNeurons] * sizeof(uint32_t));

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