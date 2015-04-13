#include "synapse_static.h"

// Common includes
#include "../common/log.h"
#include "../common/utils.h"

// Synapse processor includes
#include "ring_buffer.h"
#include "synapse_format.h"

//-----------------------------------------------------------------------------
// Module inline functions
//-----------------------------------------------------------------------------
static inline uint32_t row_count(uint32_t *row)
{
  return row[0];
}
//-----------------------------------------------------------------------------
static inline uint32_t *row_synaptic_words(uint32_t *row)
{
  return row + 1;
}

//-----------------------------------------------------------------------------
// Global functions
//-----------------------------------------------------------------------------
bool synapse_read_sdram_data(uint32_t *base_address, uint32_t flags)
{
  USE(base_address);
  USE(flags);
  return true;
}
//-----------------------------------------------------------------------------
void synapse_process_row(uint32_t tick, uint32_t *row)
{
  register uint32_t *synaptic_words = row_synaptic_words(row);
  register uint32_t count = row_count(row);

#ifdef SYNAPSE_BENCHMARK
  num_pre_synaptic_events += count;
#endif // SYNAPSE_BENCHMARK

  for(; count > 0; count--)
  {
    // Get the next 32 bit word from the synaptic_row
    // (should autoincrement pointer in single instruction)
    uint32_t synaptic_word = *synaptic_words++;

    // Extract components from this word
    uint32_t delay = synapse_format_delay(synaptic_word);
    uint32_t index = synapse_format_index(synaptic_word);
    weight_word_t weight = synapse_format_weight(synaptic_word);
  
    // Add weight to ring-buffer
    ring_buffer_add_weight(delay + tick, index, weight);
  }
}