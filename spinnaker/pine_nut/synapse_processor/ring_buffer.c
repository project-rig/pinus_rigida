#include "ring_buffer.h"

// Standard includes
#include <string.h>

//-----------------------------------------------------------------------------
// Global variables
//-----------------------------------------------------------------------------
ring_buffer_entry_t ring_buffer[RING_BUFFER_SIZE];

//-----------------------------------------------------------------------------
// Global functions
//-----------------------------------------------------------------------------
bool ring_buffer_init()
{
  // Zero ring-buffer
  memset(ring_buffer, 0, RING_BUFFER_SIZE * sizeof(ring_buffer_entry_t));
  return true;
}
//-----------------------------------------------------------------------------
void ring_buffer_clear_output_buffer(uint32_t tick)
{
  // Get output buffer for specified tick
  ring_buffer_entry_t *output_buffer;
  uint32_t output_buffer_bytes;
  ring_buffer_get_output_buffer(tick, &output_buffer, &output_buffer_bytes);
  
  // Zero it
  memset(output_buffer, 0, output_buffer_bytes);
}