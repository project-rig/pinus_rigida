
//-----------------------------------------------------------------------------
// Macros
//-----------------------------------------------------------------------------

//             |       Weights       |       Delay        |       Type        |      Index         |
//             |---------------------|--------------------|-------------------|--------------------|
// Bit count   | SYNAPSE_WEIGHT_BITS | SYNAPSE_DELAY_BITS | SYNAPSE_TYPE_BITS | SYNAPSE_INDEX_BITS |
//             |                     |                    |        SYNAPSE_TYPE_INDEX_BITS         |
//             |---------------------|--------------------|----------------------------------------|
#define SYNAPSE_TYPE_INDEX_BITS (SYNAPSE_TYPE_BITS + SYNAPSE_INDEX_BITS)

#define SYNAPSE_DELAY_MASK      ((1 << SYNAPSE_DELAY_BITS) - 1)
#define SYNAPSE_TYPE_MASK       ((1 << SYNAPSE_TYPE_BITS) - 1)
#define SYNAPSE_INDEX_MASK      ((1 << SYNAPSE_INDEX_BITS) - 1)
#define SYNAPSE_TYPE_INDEX_MASK ((1 << SYNAPSE_TYPE_INDEX_BITS) - 1)


//-----------------------------------------------------------------------------
// Module inline functions
//-----------------------------------------------------------------------------
static inline uint32_t synapse_type_index(uint32_t w)
{ 
  return (w & SYNAPSE_TYPE_INDEX_MASK); 
}
//-----------------------------------------------------------------------------
static inline uint32_t synapse_delay(uint32_t w)
{ 
  return ((w >> SYNAPSE_TYPE_INDEX_BITS) & SYNAPSE_DELAY_MASK); 
}
//-----------------------------------------------------------------------------
static inline weight_t synapse_weight(uint32_t w)
{ 
  return (w >> (32 - SYNAPSE_WEIGHT_BITS)); 
}
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
  
}
//-----------------------------------------------------------------------------
void synapse_process_row(uint32_t tick, uint32_t *row)
{
  register uint32_t *synaptic_words = row_synaptic_words(row);
  register uint32_t count = row_count(row);
  //register ring_entry_t *rp = ring_buffer;

#ifdef SYNAPSE_BENCHMARK
  num_pre_synaptic_events += count;
#endif // SYNAPSE_BENCHMARK

  for(; count > 0; count--)
  {
    // Get the next 32 bit word from the synaptic_row
    // (should autoincrement pointer in single instruction)
    uint32_t synaptic_word = *synaptic_words++;

    // Extract components from this word
    uint32_t delay = synapse_delay(synaptic_word);
    uint32_t post_index = synapse_type_index(synaptic_word);
    uint32_t weight = synapse_weight(synaptic_word);

    // Convert into ring buffer offset
    uint32_t offset = offset_sparse(delay + tick, post_index);

    // Store saturated value back in ring-buffer
    rp[offset] = rp[offset] + weight;
  }
}