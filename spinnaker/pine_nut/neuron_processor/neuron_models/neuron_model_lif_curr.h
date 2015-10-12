#ifndef NEURON_MODEL_LIF_CURR_H
#define NEURON_MODEL_LIF_CURR_H

// Standard includes
#include <stdfix.h>
#include <stdint.h>

//-----------------------------------------------------------------------------
// Structures
//-----------------------------------------------------------------------------
typedef struct neuron_t 
{
  // Membrane voltage threshold at which neuron spikes [mV]
  accum V_thresh;

  // Post-spike reset membrane voltage [mV]
  accum V_reset;

  // Membrane resting voltage [mV]
  accum V_rest;

  // Membrane resistance [some multiplier of Ohms, TBD probably MegaOhm]
  accum R_membrane;

  // Membrane voltage [mV]
  accum V_membrane;

  // Offset current [nA] but take care because actually 'per timestep charge'
  accum I_offset;

  // 'Fixed' computation parameter - time constant multiplier for
  // Closed-form solution
  // exp( -(machine time step in ms)/(R * C) ) [.]
  accum exp_TC;

  // Countdown to end of next refractory period [ms/10]
  int32_t refract_timer;

  // Refractory time of neuron [ms/10]
  int32_t T_refract;
} neuron_t;

//-----------------------------------------------------------------------------
// Global variables
//-----------------------------------------------------------------------------
extern uint32_t neuron_model_refractory_time_update;

//-----------------------------------------------------------------------------
// Inline functions
//-----------------------------------------------------------------------------
static inline bool neuron_model_update(neuron_t *neuron, accum exc_input, accum inh_input,
  accum external_input) 
{
  bool spike = false;

  // Update refractory timer
  neuron->refract_timer -= neuron_model_refractory_time_update;

  // If outside of the refractory period
  if (neuron->refract_timer <= 0) 
  {
    // Get the input in nA
    accum input_this_timestep = exc_input - inh_input
      + external_bias + neuron->I_offset;
  
    // Convert input from current to voltage 
    accum alpha = (input_this_timestep * neuron->R_membrane) + neuron->V_rest;
  
    // Perform closed form update
    neuron->V_membrane = alpha - (neuron->exp_TC * (alpha - neuron->V_membrane));

    // Neuron spikes if membrane voltage has crossed threshold
    // **YUCK** comparison operations on accums is slow
    spike = (bitsk(neuron->V_membrane) >= bitsk(neuron->V_thresh));
    if (spike) 
    {
      // Reset membrane voltage
      neuron->V_membrane = neuron->V_reset;

      // Reset refractory timer
      neuron->refract_timer  = neuron->T_refract;
    }
  }
  return spike;
}
//-----------------------------------------------------------------------------
static inline accum neuron_model_get_analogue_2(const neuron_t *neuron)
{
  return neuron->V_membrane;
}

//-----------------------------------------------------------------------------
// Global functions
//-----------------------------------------------------------------------------
void neuron_model_set_timestep(uint32_t microsecs);
void neuron_model_print(neuron_t *neuron);

#endif // NEURON_MODEL_LIF_CURR_H

