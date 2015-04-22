#ifndef SPIKE_SOURCE_H
#define SPIKE_SOURCE_H

// Standard includes
#include <stdbool.h>
#include <stdint.h>

// Sark includes
#include <sark.h>

//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indexes of application words
typedef enum app_word_e
{
  app_word_spike_history_recording_region_size,
  app_word_key,
  app_word_simulation_duration,
  app_word_timer_period,
  app_word_num_sources,
  app_word_max,
} app_word_e;

//-----------------------------------------------------------------------------
// Global variables
//-----------------------------------------------------------------------------
extern uint32_t spike_source_key;
extern uint32_t spike_source_num_sources;
extern uint32_t spike_source_app_words[app_word_max];

//-----------------------------------------------------------------------------
// Global functions provided by spike source
//-----------------------------------------------------------------------------
bool spike_source_read_sdram_data(uint32_t *base_address, uint32_t flags);
void spike_source_dma_transfer_done(uint unused, uint tag);
void spike_source_generate(uint32_t tick);

#endif  // SPIKE_SOURCE_H
