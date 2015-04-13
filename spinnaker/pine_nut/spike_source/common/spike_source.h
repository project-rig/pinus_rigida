#ifndef SPIKE_SOURCE_H
#define SPIKE_SOURCE_H

// Standard includes
#include <stdbool.h>
#include <stdint.h>

//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indexes of synapse executable regions
typedef enum region_e
{
  region_system             = 0,
  region_spike_source       = 8,
  region_record_spikes      = 14,
  region_profiler           = 17,
} region_e;

// Indexes of application words
typedef enum app_word_e
{
  app_word_spike_history_recording_region_size,
  app_word_key,
  app_word_num_sources,
  app_word_max,
} app_word_e;

//-----------------------------------------------------------------------------
// Global variables
//-----------------------------------------------------------------------------
extern uint32_t spike_source_key;
extern uint32_t spike_source_num_sources;
extern uint32_t spike_source_app_words[app_word_max];

#endif  // SPIKE_SOURCE_H
