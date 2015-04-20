#include "synapse_processor.h"

// Standard includes
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

// Spin1 includes
#include <spin1_api.h>

// Common includes
#include "../common/config.h"
#include "../common/log.h"
#include "../common/spike_input_buffer.h"
#include "../common/utils.h"

// Synapse processor includes
#include "ring_buffer.h"

//-----------------------------------------------------------------------------
// Macros
//-----------------------------------------------------------------------------
#ifndef SPIKE_INPUT_BUFFER_SIZE
  #define SPIKE_INPUT_BUFFER_SIZE 256
#endif

//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// DMA tags
typedef enum dma_tag_e
{
  dma_tag_row_read      = 0,
  dma_tag_row_write     = 1,
  dma_tag_output_write  = 2,
} dma_tag_e;

//-----------------------------------------------------------------------------
// Module variables
//-----------------------------------------------------------------------------
static bool dma_busy;
static uint32_t dma_row_buffer[2][SYNAPSE_MAX_ROW_WORDS + 1];
static uint32_t dma_row_buffer_index;
static uint32_t tick;

static uint32_t *output_buffers[2];

//-----------------------------------------------------------------------------
// Module inline functions
//-----------------------------------------------------------------------------
static inline uint32_t *dma_current_row_buffer() 
{
  return (dma_row_buffer[dma_row_buffer_index]);
}
//-----------------------------------------------------------------------------
static inline uint32_t *dma_next_row_buffer()
{
  return (dma_row_buffer[dma_row_buffer_index ^ 1]); 
}
//-----------------------------------------------------------------------------
static inline void dma_swap_row_buffers()
{
  dma_row_buffer_index ^= 1; 
}

//-----------------------------------------------------------------------------
// Module functions
//-----------------------------------------------------------------------------
static bool read_output_buffer_region(uint32_t *region, uint32_t flags)
{
  USE(flags);
  
  // Copy two output buffer pointers from region
  memcpy(output_buffers, region, 2 * sizeof(uint32_t*));
  
#if LOG_LEVEL <= LOG_LEVEL_INFO
  LOG_PRINT(LOG_LEVEL_INFO, "output_buffer\n");
  LOG_PRINT(LOG_LEVEL_INFO, "------------------------------------------\n");
  for (uint32_t i = 0; i < 2; i++)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "index %u, buffer:%p\n", i, output_buffers[i]);
  }
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
    flags, 0, NULL))
  {
    return false;
  }
  
  // Read row-lookup type-dependent regions
  if(!row_lookup_read_sdram_data(base_address, flags))
  {
    return false;
  }
  
  // Read synapse type-dependent regions
  if(!synapse_read_sdram_data(base_address, flags))
  {
    return false;
  }
  
  // Read output buffer region
  if(!read_output_buffer_region(
    config_get_region_start(region_output_buffer, base_address), 
    flags))
  {
    return false;
  }

  return true;
}
//-----------------------------------------------------------------------------
static void setup_next_dma_row_read()
{
  // If there's more incoming spikes
  uint32_t spike;
  if(spike_input_buffer_next_spike(&spike))
  {
    // Decode spike to get address of destination synaptic row
    uint32_t *address;
    uint32_t size_bytes;
    if(row_lookup_get_address(spike, &address, &size_bytes) != NULL)
    {
      // Write the SDRAM address and originating spike to the beginning of dma buffer
      dma_current_row_buffer()[0] = (uint32_t)address;

      // Start a DMA transfer to fetch this synaptic row into current buffer
      spin1_dma_transfer(dma_tag_row_read, address, &dma_current_row_buffer()[1], DMA_READ, size_bytes);

      // Flip DMA buffers
      dma_swap_row_buffers();
      
      return;
    }
  }

  dma_busy = false;
}

//-----------------------------------------------------------------------------
// Event handler functions
//-----------------------------------------------------------------------------
static void mc_packet_received(uint key, uint payload)
{
  USE(payload);

  LOG_PRINT(LOG_LEVEL_TRACE, "Received spike %x at %u, DMA Busy = %u\n", 
    key, tick, dma_busy);

  // If there was space to add spike to incoming spike queue
  if(spike_input_buffer_add_spike(key))
  {
    // If we're not already processing synaptic dmas, flag pipeline as busy and trigger a user event
    if(!dma_busy)
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
    }
  } 

}
//-----------------------------------------------------------------------------
static void dma_transfer_done(uint unused, uint tag)
{
  USE(unused);
  
  if(tag == dma_tag_row_read)
  {
    // Process row
    synapse_process_row(tick, dma_next_row_buffer() + 1);
    
    // Setup next row read
    setup_next_dma_row_read();
  }
  else if(tag == dma_tag_output_write)
  {
    ring_buffer_clear_output_buffer(tick);
  }
  else if(tag != dma_tag_row_write)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Dma transfer done with unknown tag %u\n", tag);
  }
}
//-----------------------------------------------------------------------------
void user_event(uint unused0, uint unused1)
{
  USE(unused0);
  USE(unused1);

  // Setup next row read
  setup_next_dma_row_read();
}
//-----------------------------------------------------------------------------
void timer_tick(uint unused0, uint unused1)
{
  USE(unused0);
  USE(unused1);
  
  // Increment tick counter
  tick++;
  
  LOG_PRINT(LOG_LEVEL_TRACE, "Timer tick %u, writing 'back' of ring-buffer to output buffer %u (%p)\n", 
    tick, (tick % 2), output_buffers[tick % 2]);
  
  // Get output buffer from 'back' of ring-buffer
  ring_buffer_entry_t *output_buffer;
  uint32_t output_buffer_bytes;
  ring_buffer_get_output_buffer(tick, &output_buffer, &output_buffer_bytes);
  
  // DMA output buffer into correct output buffer for this timer tick
  spin1_dma_transfer(dma_tag_output_write,
    output_buffers[tick % 2],
    output_buffer,
    DMA_WRITE,
    output_buffer_bytes);
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
  dma_busy = false;
  dma_row_buffer_index = 0;
  tick = UINT32_MAX;
  
  // Initialize modules
  ring_buffer_init();
  spike_input_buffer_init(SPIKE_INPUT_BUFFER_SIZE);
  
  // Register callbacks
  spin1_callback_on(MC_PACKET_RECEIVED, mc_packet_received, -1);
  spin1_callback_on(DMA_TRANSFER_DONE,  dma_transfer_done,  0);
  spin1_callback_on(USER_EVENT,         user_event,         0);
  spin1_callback_on(TIMER_TICK,         timer_tick,         2);
  
  // Start simulation
  spin1_start(SYNC_WAIT);
}