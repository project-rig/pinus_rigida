#ifndef RING_BUFFER_H
#define RING_BUFFER_H

// Standard includes
#include <stdbool.h>
#include <stdint.h>

// Common includes
#include "../common/utils.h"

// Synapse processor includes
#include "synapse_format.h"

//-----------------------------------------------------------------------------
// Macros
//-----------------------------------------------------------------------------
#ifndef RING_ENTRY_BITS
  #define RING_ENTRY_BITS 32
#endif

#ifdef  SYNAPSE_WEIGHTS_SIGNED
  typedef INT(RING_ENTRY_BITS)  ring_buffer_entry_t;
#else
  typedef UINT(RING_ENTRY_BITS) ring_buffer_entry_t;
#endif

#define RING_BUFFER_SIZE  (1 << (SYNAPSE_DELAY_BITS + SYNAPSE_INDEX_BITS))

//-----------------------------------------------------------------------------
// Global variables
//-----------------------------------------------------------------------------
extern ring_buffer_entry_t ring_buffer[RING_BUFFER_SIZE];

//-----------------------------------------------------------------------------
// Inline functions
//-----------------------------------------------------------------------------
static inline uint32_t ring_buffer_offset_time(uint32_t tick)
{
  return ((tick & SYNAPSE_DELAY_MASK) << SYNAPSE_INDEX_BITS);
}
//-----------------------------------------------------------------------------
static inline uint32_t ring_buffer_offset_type_index(uint32_t tick, uint32_t index)
{
  return ring_buffer_offset_time(tick) | index; 
}
//-----------------------------------------------------------------------------
static inline void ring_buffer_add_weight(uint32_t tick, uint32_t index, 
  weight_word_t weight)
{
  // Calculate ring buffer offset
  uint32_t offset = ring_buffer_offset_type_index(tick, index);

  // Add value to ring-buffer
  ring_buffer[offset] = ring_buffer[offset] + weight;
}
//-----------------------------------------------------------------------------
static inline void ring_buffer_get_output_buffer(uint32_t tick, 
  ring_buffer_entry_t **buffer, uint32_t *buffer_bytes)
{
  // Calculate ring-buffer offset for this time
  uint32_t offset = ring_buffer_offset_time(tick);
  
  // Return buffer and buffer size in bytes
  *buffer = ring_buffer + offset;
  *buffer_bytes = sizeof(ring_buffer_entry_t) * (1 << SYNAPSE_INDEX_BITS);
}

//-----------------------------------------------------------------------------
// Global functions
//-----------------------------------------------------------------------------
bool ring_buffer_init();
void ring_buffer_clear_output_buffer(uint32_t tick);

#endif  // RING_BUFFER_H