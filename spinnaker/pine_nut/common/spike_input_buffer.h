#ifndef SPIKES_INPUT_BUFFER_H
#define SPIKES_INPUT_BUFFER_H

// Standard includes
#include <stdbool.h>
#include <stdint.h>

//-----------------------------------------------------------------------------
// Global variables
//-----------------------------------------------------------------------------
extern uint32_t *spike_input_buffer;
extern uint32_t spike_input_buffer_size;

extern uint32_t spike_input_buffer_output;
extern uint32_t spike_input_buffer_input;
extern uint32_t spike_input_buffer_overflows;
extern uint32_t spike_input_buffer_underflows;

//-----------------------------------------------------------------------------
// Inline functions
//-----------------------------------------------------------------------------
// unallocated
//
// Returns the number of buffer slots currently unallocated
static inline uint32_t spike_input_buffer_unallocated()
{ 
  return ((spike_input_buffer_input - spike_input_buffer_output) % 
    spike_input_buffer_size); 
}
//-----------------------------------------------------------------------------
// allocated
//
// Returns the number of buffer slots currently allocated
static inline uint32_t spike_input_buffer_allocated()
{ 
  return ((spike_input_buffer_output - spike_input_buffer_input - 1) % 
    spike_input_buffer_size); 
}
//-----------------------------------------------------------------------------
// The following two functions are used to determine whether a
// buffer can have an element extracted/inserted respectively.
static inline bool spike_input_buffer_non_empty()
{ 
  return (spike_input_buffer_allocated() > 0);
}
//-----------------------------------------------------------------------------
static inline bool spike_input_buffer_non_full()
{
  return (spike_input_buffer_unallocated() > 0); 
}
//-----------------------------------------------------------------------------
static inline bool spike_input_buffer_add_spike(uint32_t e)
{
  bool success = spike_input_buffer_non_full();

  if (success) 
  {
    spike_input_buffer[spike_input_buffer_input] = e;
    spike_input_buffer_input = (spike_input_buffer_input - 1) % spike_input_buffer_size;
  }
  else
  {
    spike_input_buffer_overflows++;
  }

  return success;
}
//-----------------------------------------------------------------------------
static inline bool spike_input_buffer_next_spike(uint32_t *e)
{
  bool success = spike_input_buffer_non_empty();

  if (success) 
  {
    *e = spike_input_buffer[spike_input_buffer_output];
    spike_input_buffer_output = (spike_input_buffer_output - 1) % spike_input_buffer_size;
  }
  else
  {
    spike_input_buffer_underflows++;
  }
  
  return (success);
}

//-----------------------------------------------------------------------------
// Global functions
//-----------------------------------------------------------------------------
void spike_input_buffer_init(uint32_t size);

#endif  // SPIKES_INPUT_BUFFER_H