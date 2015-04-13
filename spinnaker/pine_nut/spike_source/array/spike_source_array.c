#include "../common/spike_source_impl.h"
 
// Standard includes
#include <string.h>

//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
typedef enum state_e
{
  state_inactive,
  state_dma_in_progress,
  state_spike_block_in_buffer,
} state_e;

//-----------------------------------------------------------------------------
// Module variables
//-----------------------------------------------------------------------------
// Address (SDRAM) of spike data
static uint32_t *spike_data_region_base = NULL;

// Time the next spike block should be fetched at
static uint32_t next_spike_tick = 0;

// Offset from spike_data_region_base of next spike block in bytes
static uint32_t next_spike_block_offset_bytes = 0;

// DTCM-allocated buffer, bit-vectors of outgoing spikes are made into
static uint32_t *dma_buffer = NULL;
static state_e state = state_inactive;

// Size of each timestep's spike vector in bytes
static uint32_t spike_vector_bytes = 0;

//-----------------------------------------------------------------------------
// Inline functions
//-----------------------------------------------------------------------------
static inline uint32_t get_next_spike_block_start()
{
  return (uint32_t*)((uint32_t)spike_data_region_base + 
    next_spike_block_offset_bytes);
}

//-----------------------------------------------------------------------------
// Module functions
//-----------------------------------------------------------------------------
static bool bool read_spike_source_region(uint32_t *region, uint32_t flags)
{
  use(flags);
  
  // Read the time of the next spike block and store pointer to the start of the spike data region
  next_spike_tick = region[0];
  next_spike_block_offset_bytes = region[1]
  spike_data_region_base = region + 2;
  
  log_info("\tStart address = %08x", spike_data_region_base);
  
  log_info("spike_source_spike_vector_filled: completed successfully");
  return true;
}

//-----------------------------------------------------------------------------
// Global functions
//-----------------------------------------------------------------------------
bool spike_source_read_sdram_data(uint32_t *base_address, uint32_t flags)
{
  USE(flags);

  log_info("spike_source_data_filled: starting");
  
  log_info("spike_source_spike_vector_filled: starting");
  
  // Read spike source region
  if(!read_spike_source_region(
    config_get_region_start(region_spike_source, base_address), 
    flags))
  {
    return false;
  }
  
  // Convert number of neurons to required number of blocks
  // **NOTE** in floating point terms this is ceil(num_neurons / 32)
  const uint32_t neurons_to_blocks_shift = 5;
  const uint32_t neurons_to_blocks_remainder = (1 << neurons_to_blocks_shift) - 1;
  uint32_t spike_vector_words = spike_source_app_words[app_word_num_sources] >> 5;
  if((spike_source_app_words[app_word_num_sources] & neurons_to_blocks_remainder) != 0)
  {
    spike_vector_words++;
  }
  
  // Convert this to bytes
  spike_vector_bytes = spike_vector_words * sizeof(uint32_t);
  
  // Allocate correctly sized DMA buffer
  dma_buffer = (uint32_t*)spin1_malloc(spike_vector_bytes);
  
  // If the next spike occurs in the 1st timestep
  if(next_spike_tick == 0)
  {
    // Synchronously copy next block into dma buffer
    memcpy(dma_buffer, get_next_spike_block_start(), spike_vector_bytes);
    
    // Set state to reflect that there is data already in the buffer
    state = state_spike_block_in_buffer;
  }
  
  log_info("spike_source_data_filled: completed successfully");
  
  return true;
}
//-----------------------------------------------------------------------------
void spike_source_dma_transfer_done(uint unused, uint tag)
{
  use(unused);
  
  if (tag != 0)
  {
    sentinel("tag (%d) = 0", tag);
  }
  
  if(state != state_dma_in_progress)
  {
    sentinel("state (%u) = %u", state, state_dma_in_progress);
  }
  
  log_info("DMA transfer complete");
  
  // Set state to reflect that the spike block is now in the buffer
  state = state_spike_block_in_buffer;
}
//-----------------------------------------------------------------------------
void spike_source_generate(uint32_t tick)
{
  // If a spike block has been transferred ready for this tick
  if(next_spike_tick == tick)
  {
    // If there is data in the buffer
    if(state == e_state_spike_block_in_buffer)
    {
      // **TODO** send spikes
      
      // Update next spike
      next_spike_tick = dma_buffer[0];
      next_spike_block_offset_bytes = dma_buffer[1];
      
      // Set state to inactive
      state = state_inactive;
    }
    // Otherwise error
    else
    {
      log_info("ERROR: DMA hasn't completed in time for next tick");
    }
  }
  
  // If the next spike should be sent next tick
  if(next_spike_tick == (tick + 1))
  {
    // Start a DMA transfer from the absolute address of the spike block into buffer
    spin1_dma_transfer(0, get_next_spike_block_start(), dma_buffer, DMA_READ, spike_vector_bytes);
    
    // Set state to dma in progress
    state = e_state_dma_in_progress;
  }
}