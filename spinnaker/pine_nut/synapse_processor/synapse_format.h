#ifndef SYNAPSE_FORMAT_H
#define SYNAPSE_FORMAT_H

//-----------------------------------------------------------------------------
// Macros
//-----------------------------------------------------------------------------
//             |       Weights       |       Delay        |       Type        |      Index         |
//             |---------------------|--------------------|-------------------|--------------------|
// Bit count   | SYNAPSE_WEIGHT_BITS | SYNAPSE_DELAY_BITS | SYNAPSE_TYPE_BITS | SYNAPSE_INDEX_BITS |
//             |                     |                    |        SYNAPSE_TYPE_INDEX_BITS         |
//             |---------------------|--------------------|----------------------------------------|

// Synaptic format component bit counts
#ifndef SYNAPSE_INDEX_BITS
  #define SYNAPSE_INDEX_BITS 8
#endif

#ifndef SYNAPSE_DELAY_BITS
  #define SYNAPSE_DELAY_BITS 3
#endif

#ifndef SYNAPSE_WEIGHT_BITS
  #define SYNAPSE_WEIGHT_BITS 16
#endif

#define SYNAPSE_TYPE_INDEX_BITS  (SYNAPSE_TYPE_BITS + SYNAPSE_INDEX_BITS)

// Define synaptic weight type
#ifdef  SYNAPSE_WEIGHTS_SIGNED
  typedef int32_t weight_word_t;
  typedef  __int_t(SYNAPSE_WEIGHT_BITS) weight_t;
#else
  typedef uint32_t weight_word_t;
  typedef __uint_t(SYNAPSE_WEIGHT_BITS) weight_t;
#endif

// Synapse word component masks derived from synapse bit format
#define SYNAPSE_DELAY_MASK      ((1 << SYNAPSE_DELAY_BITS) - 1)
#define SYNAPSE_TYPE_MASK       ((1 << SYNAPSE_TYPE_BITS) - 1)
#define SYNAPSE_INDEX_MASK      ((1 << SYNAPSE_INDEX_BITS) - 1)
#define SYNAPSE_TYPE_INDEX_MASK ((1 << SYNAPSE_TYPE_INDEX_BITS) - 1)

//-----------------------------------------------------------------------------
// Inline functions
//-----------------------------------------------------------------------------
static inline uint32_t synapse_format_type_index(uint32_t w)
{ 
  return (w & SYNAPSE_TYPE_INDEX_MASK); 
}
//-----------------------------------------------------------------------------
static inline uint32_t synapse_format_delay(uint32_t w)
{ 
  return ((w >> SYNAPSE_TYPE_INDEX_MASK) & SYNAPSE_DELAY_MASK); 
}
//-----------------------------------------------------------------------------
static inline weight_t synapse_format_weight(uint32_t w)
{ 
  return (w >> (32 - SYNAPSE_WEIGHT_BITS)); 
}

#endif  // SYNAPSE_FORMAT_H