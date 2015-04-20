// Standard includes
#include <string.h>

// Spin1 includes
#include <spin1_api.h>

// Common includes
#include "../../common/bit_field.h"
#include "../../common/config.h"
#include "../../common/log.h"
#include "../../common/utils.h"

// Spike source includes
#include "../common/spike_source.h"

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

static uint32_t next_spike_block_offset_words = 0;

// DTCM-allocated buffer, bit-vectors of outgoing spikes are made into
static uint32_t *dma_buffer = NULL;
static state_e state = state_inactive;

// Size of each timestep's spike vector in words
static uint32_t spike_block_size_words = 0;

//-----------------------------------------------------------------------------
// Module functions
//-----------------------------------------------------------------------------
static bool read_spike_source_region(uint32_t *region, uint32_t flags)
{
  USE(flags);
  
  // Read the time of the next spike block and store pointer to the start of the spike data region
  next_spike_tick = region[0];
  spike_data_region_base = region + 1;
  
  LOG_PRINT(LOG_LEVEL_INFO, "\tnext_spike_tick:%u, spike_data_region_base:%p \n", next_spike_tick, spike_data_region_base);
  return true;
}

//-----------------------------------------------------------------------------
// Global functions
//-----------------------------------------------------------------------------
bool spike_source_read_sdram_data(uint32_t *base_address, uint32_t flags)
{
  USE(flags);
  
  LOG_PRINT(LOG_LEVEL_INFO, "spike_source_read_sdram_data\n");
  
  // Read spike source region
  if(!read_spike_source_region(
    config_get_region_start(region_spike_source, base_address), 
    flags))
  {
    return false;
  }
  
  // Determine how many words are required for each neuron to have a bit
  // **NOTE** add one for word containing tick next dma is required at
  spike_block_size_words = bit_field_get_word_size(spike_source_app_words[app_word_num_sources]) + 1;
  LOG_PRINT(LOG_LEVEL_INFO, "\tspike_block_size_words %u\n", spike_block_size_words);
  
  // Allocate correctly sized DMA buffer
  dma_buffer = (uint32_t*)spin1_malloc(spike_block_size_words * sizeof(uint32_t));
  
  // If the next spike occurs in the 1st timestep
  if(next_spike_tick == 0)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "Copying first block into DMA buffer synchronously\n");
    
    // Synchronously copy next block into dma buffer
    memcpy(dma_buffer, spike_data_region_base, spike_block_size_words * sizeof(uint32_t));
    next_spike_block_offset_words += spike_block_size_words;
    
    // Set state to reflect that there is data already in the buffer
    state = state_spike_block_in_buffer;
  }
  
  LOG_PRINT(LOG_LEVEL_INFO, "spike_source_read_sdram_data: completed successfully\n");
  
  return true;
}
//-----------------------------------------------------------------------------
void spike_source_dma_transfer_done(uint unused, uint tag)
{
  USE(unused);
  
  if(tag != 0)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "tag (%d) = 0\n", tag);
  }
  
  if(state != state_dma_in_progress)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "state (%u) = %u\n", state, state_dma_in_progress);
  }
  
  LOG_PRINT(LOG_LEVEL_TRACE, "DMA transfer complete\n");
  
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
    if(state == state_spike_block_in_buffer)
    {
      // Loop through sources
      for(uint s = 0; s < spike_source_app_words[app_word_num_sources]; s++)
      {
        // If this source has spiked
        if(bit_field_test_bit(dma_buffer + 1, spike_block_size_words - 1))
        {
          uint32_t key = spike_source_app_words[app_word_key] | s;
          while(!spin1_send_mc_packet(key, 0, NO_PAYLOAD)) 
          {
              spin1_delay_us(1);
          }
        }
      }
      
      // Update next spike tick from start of block and 
      // Advance offset to next block to fetch
      next_spike_tick = dma_buffer[0];
      next_spike_block_offset_words += spike_block_size_words;
      
      // Set state to inactive
      state = state_inactive;
    }
    // Otherwise error
    else
    {
      LOG_PRINT(LOG_LEVEL_WARN, "DMA hasn't completed in time for next tick\n");
    }
  }
  
  // If the next spike should be sent next tick
  if(next_spike_tick == (tick + 1))
  {
    // Start a DMA transfer from the absolute address of the spike block into buffer
    spin1_dma_transfer(0, spike_data_region_base + next_spike_block_offset_words, 
      dma_buffer, DMA_READ, spike_block_size_words * sizeof(uint32_t));
    
    // Set state to dma in progress
    state = state_dma_in_progress;
  }
}