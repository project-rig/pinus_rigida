#ifndef NEURON_PROCESSOR_H
#define NEURON_PROCESSOR_H


//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indexes of application words
typedef enum app_word_e
{
  app_word_key,
  app_word_simulation_duration,
  app_word_timer_period,
  app_word_timestep,
  app_word_num_neurons,
  app_word_max,
} app_word_e;

#endif  // NEURON_PROCESSOR_H