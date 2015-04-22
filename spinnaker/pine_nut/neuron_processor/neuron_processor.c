#include "neuron_processor.h"

// Standard includes
#include <string.h>

//-----------------------------------------------------------------------------
// Module variables
//-----------------------------------------------------------------------------
static uint32_t app_words[app_word_max];
static neuron_t *neurons = NULL;

//-----------------------------------------------------------------------------
// Module functions
//-----------------------------------------------------------------------------
static bool read_neuron_region(uint32_t *region, uint32_t flags)
{
  USE(flags);
  
  // Allocate array for neurons
  uint32_t neuron_bytes = sizeof(neuron_t) * app_words[app_word_num_neurons];
  neurons = spin1_malloc(neuron_bytes);
  if(neurons == NULL)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate %u byte neuron array\n", 
      neuron_bytes);
    return false;
  }
  
  // Copy neuron data into newly allocated array
  memcpy(neurons, region, neuron_bytes);
  
#if LOG_LEVEL <= LOG_LEVEL_INFO
  LOG_PRINT(LOG_LEVEL_INFO, "neurons\n");
  LOG_PRINT(LOG_LEVEL_INFO, "------------------------------------------\n");
  //for (uint32_t i = 0; i < 2; i++)
  //{
  //  LOG_PRINT(LOG_LEVEL_INFO, "index %u, buffer:%p\n", i, output_buffers[i]);
  //}
  LOG_PRINT(LOG_LEVEL_INFO, "------------------------------------------\n");
#endif
  
  return true;
}
//-----------------------------------------------------------------------------
static bool read_sdram_data(uint32_t *base_address, uint32_t flags)
{
  // Read data header
  uint32_t version;
  if(!config_read_header(base_address, &version, flags))
  {
    return false;
  }

  // Read system region
  if(!config_read_system_region(
    config_get_region_start(region_system, base_address), 
    flags, app_word_max, app_words))
  {
    return false;
  }
  
  // Read neuron region
  if(!read_neuron_region(
    config_get_region_start(region_neuron, base_address), flags))
  {
    return false;
  }

  return true;
}

//-----------------------------------------------------------------------------
// Event handler functions
//-----------------------------------------------------------------------------
static void dma_transfer_done(uint unused, uint tag)
{
  USE(unused);
  
  if(tag == dma_tag_input_read)
  {
    
  }
  else
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Dma transfer done with unknown tag %u\n", tag);
  }
}
//-----------------------------------------------------------------------------
static void timer_tick(uint unused0, uint unused1)
{
  USE(unused0);
  USE(unused1);
  
  // Increment tick counter
  tick++;
  
  // If a fixed number of simulation ticks are specified and these have passed
  if (app_words[app_word_simulation_duration] != UINT32_MAX 
    && tick >= app_words[app_word_simulation_duration])
  {
    LOG_PRINT(LOG_LEVEL_INFO, "Simulation complete\n");

    // Finalise any recordings that are in progress, writing back the final amounts of samples recorded to SDRAM
    //recording_finalise();
    spin1_exit(0);
  }
  
  // Loop through neurons
  for(uint n = 0; n < app_words[app_word_num_neurons]; n++)
  {
    neuron_t *neuron = neurons[n];
    
    // Update neuron, if it spikes
    accum exc_input = 0.0k;
    accum inh_input = 0.0k;
    accum external_input = 0.0k;
    if(neuron_model_update(neuron, exc_input, inh_input, external_input))
    {
      // Send spike
      uint32_t key = spike_source_app_words[app_word_key] | n;
      while(!spin1_send_mc_packet(key, 0, NO_PAYLOAD)) 
      {
        spin1_delay_us(1);
      }
    }
  }
}


//-----------------------------------------------------------------------------
// Entry point
//-----------------------------------------------------------------------------
void c_main()
{
  // Get this core's base address
  uint32_t *base_address = config_get_base_address();
  
  // If reading SDRAM data fails
  if(!read_sdram_data(base_address, 0))
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Error reading SDRAM data\n");
    return;
  }
  
  // Initialise 
  // **NOTE** tick is initialized to UINT32_MAX as ticks are advanced at
  // The START of each timer tick so it will be zeroed once time 'starts'
  tick = UINT32_MAX;
  
  // Set timer tick (in microseconds) in both timer and 
  spin1_set_timer_tick(app_words[app_word_timer_period]);
  neuron_model_set_timestep(app_words[app_word_timestep]);
  
  // Register callbacks
  spin1_callback_on(DMA_TRANSFER_DONE,  dma_transfer_done,  0);
  spin1_callback_on(TIMER_TICK,         timer_tick,         2);
  
  // Start simulation
  spin1_start(SYNC_WAIT);
}