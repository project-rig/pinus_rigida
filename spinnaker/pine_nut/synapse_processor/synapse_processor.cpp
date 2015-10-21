#include "synapse_processor.h"

// Common includes
#include "../common/config.h"
#include "../common/log.h"
#include "../common/spinnaker.h"

// Configuration include
#include "config.h"

// Namespaces
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
};

//----------------------------------------------------------------------------
// Module level variables
//----------------------------------------------------------------------------
Common::Config g_Config;
RingBuffer g_RingBuffer;
SpikeInputBuffer g_SpikeInputBuffer;

uint32_t g_AppWords[AppWordMax];

uint32_t *g_OutputBuffers[2] = {NULL, NULL};

//-----------------------------------------------------------------------------
// Module variables
//-----------------------------------------------------------------------------
/*static bool dma_busy;
static uint32_t dma_row_buffer[2][SYNAPSE_MAX_ROW_WORDS + 1];
static uint32_t dma_row_buffer_index;

static uint32_t *output_buffers[2];


//-----------------------------------------------------------------------------
// Module inline functions
//-----------------------------------------------------------------------------
inline uint32_t *dma_current_row_buffer()
{
  return (dma_row_buffer[dma_row_buffer_index]);
}
//-----------------------------------------------------------------------------
inline uint32_t *dma_next_row_buffer()
{
  return (dma_row_buffer[dma_row_buffer_index ^ 1]);
}
//-----------------------------------------------------------------------------
inline void dma_swap_row_buffers()
{
  dma_row_buffer_index ^= 1;
}
*/
//-----------------------------------------------------------------------------
// Module functions
//-----------------------------------------------------------------------------
bool ReadOutputBufferRegion(uint32_t *region, uint32_t)
{
  // Copy two output buffer pointers from region
  spin1_memcpy(g_OutputBuffers, region, 2 * sizeof(uint32_t*));

#if LOG_LEVEL <= LOG_LEVEL_INFO
  LOG_PRINT(LOG_LEVEL_INFO, "output_buffer\n");
  LOG_PRINT(LOG_LEVEL_INFO, "------------------------------------------\n");
  for (uint32_t i = 0; i < 2; i++)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "index %u, buffer:%p\n", i, g_OutputBuffers[i]);
  }
  LOG_PRINT(LOG_LEVEL_INFO, "------------------------------------------\n");
#endif

  return true;
}
//-----------------------------------------------------------------------------
bool ReadSDRAMData(uint32_t *baseAddress, uint32_t flags)
{
  // Verify data header
  uint32_t version;
  if(!g_Config.VerifyHeader(baseAddress, flags, version))
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

  // Read row-lookup type-dependent regions
  /*if(!row_lookup_read_sdram_data(base_address, flags))
  {
    return false;
  }

  // Read synapse type-dependent regions
  if(!synapse_read_sdram_data(base_address, flags))
  {
    return false;
  }*/

  // Read output buffer region
  if(!ReadOutputBufferRegion(
    Common::Config::GetRegionStart(baseAddress, RegionOutputBuffer),
    flags))
  {
    return false;
  }

  return true;
}
//-----------------------------------------------------------------------------
void SetupNextDMARowRead()
{
  // If there's more incoming spikes
  uint32_t spike;
  if(g_SpikeInputBuffer.GetNextSpike(&spike))
  {
    // Decode spike to get address of destination synaptic row
    /*uint32_t *address;
    uint32_t sizeBytes;
    if(row_lookup_get_address(spike, &address, &sizeBytes) != NULL)
    {
      // Write the SDRAM address and originating spike to the beginning of dma buffer
      dma_current_row_buffer()[0] = (uint32_t)address;

      // Start a DMA transfer to fetch this synaptic row into current buffer
      spin1_dma_transfer(dma_tag_row_read, address, &dma_current_row_buffer()[1], DMA_READ, sizeBytes);

      // Flip DMA buffers
      dma_swap_row_buffers();

      return;
    }*/
  }

  //dma_busy = false;
}

//-----------------------------------------------------------------------------
// Event handler functions
//-----------------------------------------------------------------------------
void MCPacketReceived(uint key, uint)
{
  //LOG_PRINT(LOG_LEVEL_TRACE, "Received spike %x at %u, DMA Busy = %u\n",
  //  key, tick, dma_busy);

  // If there was space to add spike to incoming spike queue
  if(g_SpikeInputBuffer.AddSpike(key))
  {
    // If we're not already processing synaptic dmas, flag pipeline as busy and trigger a user event
    /*if(!dma_busy)
    {
      LOG_PRINT(LOG_LEVEL_TRACE, "Triggering user event for new spike\n");

      if(spin1_trigger_user_event(0, 0))
      {
        dma_busy = true;
      }
      else
      {
        LOG_PRINT(LOG_LEVEL_WARN, "Could not trigger user event\n");
      }
    }*/
  }

}
//-----------------------------------------------------------------------------
void DMATransferDone(uint, uint tag)
{
  if(tag == DMATagRowRead)
  {
    // Process row
    //synapse_process_row(tick, dma_next_row_buffer() + 1);

    // Setup next row read
    SetupNextDMARowRead();
  }
  else if(tag == DMATagOutputWrite)
  {
    // This timesteps output has been written from the ring-buffer so we can now zero it
    //ring_buffer_clear_output_buffer(tick);
  }
  else if(tag != DMATagRowWrite)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Dma transfer done with unknown tag %u\n", tag);
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
  // If a fixed number of simulation ticks are specified and these have passed
  if(g_Config.GetSimulationTicks() != UINT32_MAX
    && tick >= g_Config.GetSimulationTicks())
  {
    LOG_PRINT(LOG_LEVEL_INFO, "Simulation complete\n");

    // Finalise any recordings that are in progress, writing back the final amounts of samples recorded to SDRAM
    //recording_finalise();
    spin1_exit(0);
  }

  LOG_PRINT(LOG_LEVEL_TRACE, "Timer tick %u, writing 'back' of ring-buffer to output buffer %u (%p)\n",
    tick, (tick % 2), g_OutputBuffers[tick % 2]);

  // Get output buffer from 'back' of ring-buffer
  const RingBuffer::Type *pOutputBuffer = g_RingBuffer.GetOutputBuffer(tick);

  // DMA output buffer into correct output buffer for this timer tick
  //spin1_dma_transfer(DMATagOutputWrite,
  //  g_OutputBuffers[tick % 2],
  //  output_buffer,
  //  DMA_WRITE,
  //  output_buffer_bytes);
}
} // anonymous namespace

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
    LOG_PRINT(LOG_LEVEL_ERROR, "Error reading SDRAM data\n");
    return;
  }

  // Initialise
  // **NOTE** tick is initialized to UINT32_MAX as ticks are advanced at
  // The START of each timer tick so it will be zeroed once time 'starts'
  //dma_busy = false;
  //dma_row_buffer_index = 0;

  // Initialize modules
  //ring_buffer_init();

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