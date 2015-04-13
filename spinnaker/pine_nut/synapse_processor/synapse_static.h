#ifndef SYNAPSE_STATIC_H
#define SYNAPSE_STATIC_H

// Standard includes
#include <stdbool.h>
#include <stdint.h>

// Synapse processor includes
#include "synapse_format.h"

//-----------------------------------------------------------------------------
// Macros
//-----------------------------------------------------------------------------
// Static synapses have no limit on number of neurons beyond the synapse format
#define SYNAPSE_MAX_POST_NEURONS  (1 << SYNAPSE_INDEX_BITS)

// For static synapse format, rows simply consts 
// Of a count followed by a word for each synapse
#define SYNAPSE_MAX_ROW_WORDS     (1 + SYNAPSE_MAX_POST_NEURONS)

//-----------------------------------------------------------------------------
// Global functions
//-----------------------------------------------------------------------------
bool synapse_read_sdram_data(uint32_t *base_address, uint32_t flags);

void synapse_process_row(uint32_t tick, uint32_t *row);

#endif  // SYNAPSE_STATIC_H