#include "spike_source.h"

// Standard includes
#include <string.h>

// Spin1 includes
#include <spin1_api.h>

// Common includes
#include "../../common/config.h"
#include "../../common/log.h"
#include "../../common/utils.h"

//-----------------------------------------------------------------------------
// Global variables
//-----------------------------------------------------------------------------
uint32_t spike_source_key = 0;
uint32_t spike_source_num_sources = 0;
uint32_t spike_source_app_words[app_word_max];

//-----------------------------------------------------------------------------
// Module variables
//-----------------------------------------------------------------------------
static uint32_t tick;

//-----------------------------------------------------------------------------
// Module functions
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
    flags, app_word_max, spike_source_app_words))
  {
    return false;
  }
  
  // Read spike source type-dependent data
  if(!spike_source_read_sdram_data(base_address, flags))
  {
    return false;
  }
  
  return true;
}
//-----------------------------------------------------------------------------
static void timer_tick(uint unused0, uint unused1)
{
  USE(unused0);
  USE(unused1);
  
  // Increment tick counter
  tick++;
  LOG_PRINT(LOG_LEVEL_TRACE, "Timer tick %u", tick);

  // If a fixed number of simulation ticks are specified and these have passed
  if (spike_source_app_words[app_word_simulation_duration] != UINT32_MAX 
    && tick >= spike_source_app_words[app_word_simulation_duration])
  {
    LOG_PRINT(LOG_LEVEL_INFO, "Simulation complete");

    // Finalise any recordings that are in progress, writing back the final amounts of samples recorded to SDRAM
    //recording_finalise();
    spin1_exit(0);
  }

  // Generate spikes
  spike_source_generate(tick);

  // Record output spikes if required
  /*record_out_spikes();

  if (nonempty_out_spikes ())
  {
#ifdef DEBUG
    print_out_spikes ();
#endif // DEBUG

#ifdef SPIKE_SOURCE_SEND_OUT_SPIKES
    for (index_t i = 0; i < num_spike_sources; i++)
    {
      if (out_spike_test (i))
      {
        log_info("Sending spike packet %x", key | i);
        spin1_send_mc_packet(key | i, NULL, NO_PAYLOAD);
        spin1_delay_us(1);
      }
    }
#endif  // SPIKE_SOURCE_SEND_OUT_SPIKES

    reset_out_spikes ();
  }*/
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
    LOG_PRINT(LOG_LEVEL_ERROR, "Error reading SDRAM data");
    return;
  }
  
  // Initialise 
  // **NOTE** tick is initialized to UINT32_MAX as ticks are advanced at
  // The START of each timer tick so it will be zeroed once time 'starts'
  tick = UINT32_MAX;

  // Set timer tick (in microseconds)
  spin1_set_timer_tick(spike_source_app_words[app_word_timer_period]);

  // Register callbacks
  spin1_callback_on(TIMER_TICK, timer_tick, 2);
  spin1_callback_on(DMA_TRANSFER_DONE, spike_source_dma_transfer_done, 0);

  // Start simulation
  spin1_start(SYNC_WAIT);
}
