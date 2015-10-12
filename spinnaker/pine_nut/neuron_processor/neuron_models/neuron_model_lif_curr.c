#include "neuron_model_lif_curr.h"

//-----------------------------------------------------------------------------
// Global variables
//-----------------------------------------------------------------------------
// for general machine time steps
// defaults to 1ms time step i.e. 10 x 1/10ths of a msec
uint32_t neuron_model_refractory_time_update = 10;

//-----------------------------------------------------------------------------
// Global functions
//-----------------------------------------------------------------------------
// setup function which needs to be called in main program before any neuron
// code executes
// MUST BE: minimum 100, then in 100usec steps...
void neuron_model_set_timestep(uint32_t microsecs)
{
  // 10 for 1ms time step, 1 for 0.1ms time step which is minimum
  neuron_model_refractory_time_update = microsecs / 100;
}
//-----------------------------------------------------------------------------
// printout of neuron definition and state variables
void neuron_model_print(neuron_t *neuron)
{
  log_debug("V membrane    = %11.4k mv", neuron->V_membrane);
  log_debug("V thresh      = %11.4k mv", neuron->V_thresh);
  log_debug("V reset       = %11.4k mv", neuron->V_reset);
  log_debug("V rest        = %11.4k mv", neuron->V_rest);

  log_debug("I offset      = %11.4k nA", neuron->I_offset);
  log_debug("R membrane    = %11.4k Mohm", neuron->R_membrane);

  log_debug("exp(-ms/(RC)) = %11.4k [.]", neuron->exp_TC);

  log_debug("T refract     = %u microsecs", neuron->T_refract * 100);
}