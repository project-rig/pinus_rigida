#ifndef RING_BUFFER_H
#define RING_BUFFER_H

// Synapse processor includes
#include "synapse_format.h"

//-----------------------------------------------------------------------------
// Macros
//-----------------------------------------------------------------------------
#ifndef RING_ENTRY_BITS
  #define RING_ENTRY_BITS 32
#endif

#ifdef  SYNAPSE_WEIGHTS_SIGNED
  typedef  __int_t(RING_ENTRY_BITS)    ring_entry_t;
#else
  typedef  __uint_t(RING_ENTRY_BITS)   ring_entry_t;
#endif

#define RING_BUFFER_SIZE  (1 << (SYNAPSE_DELAY_BITS + SYNAPSE_TYPE_INDEX_BITS))

//-----------------------------------------------------------------------------
// Global variables
//-----------------------------------------------------------------------------
extern ring_entry_t ring_buffer[RING_BUFFER_SIZE];

//-----------------------------------------------------------------------------
// Inline functions
//-----------------------------------------------------------------------------
static inline uint32_t ring_buffer_offset_time(uint32_t tick)
{
  return ((tick & SYNAPSE_DELAY_MASK) << SYNAPSE_TYPE_INDEX_BITS);
}
//-----------------------------------------------------------------------------
static inline uint32_t ring_buffer_offset_type_index(uint32_t tick, uint32_t type_index)
{
  return ring_buffer_offset_time(tick) | type_index); 
}
//-----------------------------------------------------------------------------
static inline void ring_buffer_add_weight(uint32_t tick, uint32_t type_index, 
  weight_word_t weight)
{
  // Calculate ring buffer offset
  uint32_t offset = ring_buffer_offset_type_index(tick, type_index);

  // Add value to ring-buffer
  ring_buffer[offset] = ring_buffer[offset] + weight;
}
//-----------------------------------------------------------------------------
static inline void ring_buffer_get_output_buffer(uint32_t tick, 
  ring_buffer_t **buffer, uint32_t *buffer_bytes)
{
  // Calculate ring-buffer offset for this time
  uint32_t offset = ring_buffer_offset_time(tick);
  
  // Return buffer and buffer size in bytes
  buffer = ring_buffer + offset;
  buffer_bytes = sizeof(ring_entry_t) * (1 << SYNAPSE_TYPE_INDEX_BITS);
}

//-----------------------------------------------------------------------------
// Global functions
//-----------------------------------------------------------------------------
bool ring_buffer_init();
void ring_buffer_clear_output_buffer(uint32_t tick);

#endif  // RING_BUFFER_H