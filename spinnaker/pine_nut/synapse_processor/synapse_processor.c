#include "synapse_processor.h"

// Standard includes
#include <stdbool.h>
#include <stdint.h>

// Common includes
#include "config.h"

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
static uint32_t dma_row_buffer[2][MAX_POST_NEURONS];
static uint32_t dma_row_buffer_index;
static uint32_t tick;

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
  if(!ring_buffer_read_output_buffer_region(
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
  if(next_spike(&s))
  {
    // Decode spike to get address of destination synaptic row
    uint32_t *address;
    uint32_t *size_bytes;
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
    ring_buffer_output_write_complete();
  }
  else if(tag != dma_tag_row_write)
  {
    LOG_PRINT_ERROR("Dma transfer done with unknown tag %u\n", tag);
  }
}
//-----------------------------------------------------------------------------
void timer_tick(uint unused0, uint unused1)
{
  USE(unused0);
  USE(unused1);
  
  // Increment tick counter
  tick++;
  
  
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
    LOG_PRINT_ERROR("Error reading SDRAM data\n");
    return;
  }
  
  // Initialise 
  // **NOTE** tick is initialized to UINT32_MAX as ticks are advanced at
  // The START of each timer tick so it will be zeroed once time 'starts'
  dma_busy = false;
  dma_row_buffer_index = 0;
  tick = UINT32_MAX;
  
  // Register callbacks
  spin1_callback_on(MC_PACKET_RECEIVED, mc_packet_received, -1);
  spin1_callback_on(DMA_TRANSFER_DONE,  dma_transfer_done,  0);
  spin1_callback_on(USER_EVENT,         user_event,         0);
  spin1_callback_on(TIMER_TICK,         timer_tick,         2);
  
  // Start simulation
  spin1_start(SYNC_WAIT);
  
}