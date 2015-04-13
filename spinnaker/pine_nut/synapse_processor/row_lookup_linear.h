#ifndef ROW_LOOKUP_LINEAR_H
#define ROW_LOOKUP_LINEAR_H

// Standard includes
#include <stdbool.h>
#include <stdint.h>

//-----------------------------------------------------------------------------
// Global functions
//-----------------------------------------------------------------------------
bool row_lookup_read_sdram_data(uint32_t *base_address, uint32_t flags);
bool row_lookup_get_address(uint32_t key, uint32_t **address, uint32_t *size_bytes);

#endif  // ROW_LOOKUP_LINEAR_H