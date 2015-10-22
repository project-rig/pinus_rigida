#include "neuron_processor.h"

// Common includes
#include "../common/config.h"
#include "../common/fixed_point_number.h"
#include "../common/log.h"
#include "../common/spinnaker.h"

// Configuration include
#include "config.h"

// Namespaces
using namespace Common::FixedPointNumber;
using namespace NeuronProcessor;

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
  DMATagInputRead,
};

//----------------------------------------------------------------------------
// Module level variables
//----------------------------------------------------------------------------
Common::Config g_Config;
uint32_t g_AppWords[AppWordMax];

Neuron::MutableState *g_NeuronMutableState = NULL;
Neuron::ImmutableState *g_NeuronImmutableState = NULL;

//----------------------------------------------------------------------------
// Functions
//----------------------------------------------------------------------------
bool ReadNeuronRegion(uint32_t *region, uint32_t)
{
  // Allocate array for neuron's mutable state
  // **TODO** spin1_malloc allocator
  uint32_t mutableNeuronBytes = sizeof(Neuron::MutableState) * g_AppWords[AppWordNumNeurons];
  g_NeuronMutableState = (Neuron::MutableState*)spin1_malloc(mutableNeuronBytes);
  if(g_NeuronMutableState == NULL)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate %u byte neuron mutable state array",
      mutableNeuronBytes);
    return false;
  }
  
  // Copy neuron data into newly allocated array
  spin1_memcpy(g_NeuronMutableState, region, mutableNeuronBytes);

  // Allocate array for neuron's mutable state
  uint32_t immutableNeuronBytes = sizeof(Neuron::ImmutableState) * g_AppWords[AppWordNumNeurons];
  g_NeuronImmutableState = (Neuron::ImmutableState*)spin1_malloc(immutableNeuronBytes);
  if(g_NeuronImmutableState == NULL)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate %u byte neuron imutable data array",
      immutableNeuronBytes);
    return false;
  }

  // Copy neuron data into newly allocated array
  spin1_memcpy(g_NeuronImmutableState, region, immutableNeuronBytes);
  
#if LOG_LEVEL <= LOG_LEVEL_TRACE
  LOG_PRINT(LOG_LEVEL_TRACE, "neurons");
  LOG_PRINT(LOG_LEVEL_TRACE, "------------------------------------------");
  //for (uint32_t i = 0; i < 2; i++)
  //{
  //  LOG_PRINT(LOG_LEVEL_INFO, "index %u, buffer:%p\n", i, output_buffers[i]);
  //}= NULL
  LOG_PRINT(LOG_LEVEL_TRACE, "------------------------------------------");
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
    Common::Config::GetRegionStart(baseAddress, RegionSystem),
    flags, AppWordMax, g_AppWords))
  {
    return false;
  }
  
  // Read neuron region
  if(!ReadNeuronRegion(
    Common::Config::GetRegionStart(baseAddress, RegionNeuron), flags))
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
  if(tag == DMATagInputRead)
  {
    
  }
  else
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Dma transfer done with unknown tag %u", tag);
  }
}
//-----------------------------------------------------------------------------
static void TimerTick(uint tick, uint)
{
  LOG_PRINT(LOG_LEVEL_TRACE, "Timer tick %u", tick);

  // If a fixed number of simulation ticks are specified and these have passed
  if(g_Config.GetSimulationTicks() != UINT32_MAX
    && tick >= g_Config.GetSimulationTicks())
  {
    LOG_PRINT(LOG_LEVEL_INFO, "Simulation complete");

    // Finalise any recordings that are in progress, writing back the final amounts of samples recorded to SDRAM
    //recording_finalise();
    spin1_exit(0);
  }
  
  // Loop through neurons
  auto *neuronMutableState = g_NeuronMutableState;
  auto *neuronImmutableState = g_NeuronImmutableState;
  for(uint n = 0; n < g_AppWords[AppWordNumNeurons]; n++)
  {
    // Update neuron, if it spikes
    S1615 exc_input = 0;
    S1615 inh_input = 0;
    S1615 external_input = 0;
    if(Neuron::Update(*neuronMutableState++, *neuronImmutableState++,
      exc_input, inh_input, external_input))
    {
      // Send spike
      uint32_t key = g_AppWords[AppWordKey] | n;
      while(!spin1_send_mc_packet(key, 0, NO_PAYLOAD)) 
      {
        spin1_delay_us(1);
      }
    }
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
  spin1_callback_on(DMA_TRANSFER_DONE,  DMATransferDone,  0);
  spin1_callback_on(TIMER_TICK,         TimerTick,        2);
  
  // Start simulation
  spin1_start(SYNC_WAIT);
}