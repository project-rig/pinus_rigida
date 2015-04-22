#ifndef SYNAPSE_PROCESSOR_H
#define SYNAPSE_PROCESSOR_H

//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indexes of synapse executable regions
typedef enum region_e
{
  region_system             = 0,
  region_row_size           = 3,
  region_master_population  = 4,
  region_synaptic_matrix    = 5,
  region_plasticity         = 6,
  region_output_buffer      = 7,
  region_profiler           = 17,
} region_e;

// Indexes of application words
typedef enum app_word_e
{
  app_word_simulation_duration,
  app_word_timer_period,
  app_word_max,
} app_word_e;

#endif  // SYNAPSE_PROCESSOR_H