#ifndef CONFIG_H
#define CONFIG_H

// Standard includes
#include <stdbool.h>
#include <stdint.h>

//-----------------------------------------------------------------------------
// Global functions
//-----------------------------------------------------------------------------
// Get the base address of this core's SDRAM data using allocation tag
uint32_t *config_get_base_address();

// Read header residing at the beginning of all executable's SDRAM data
bool config_read_header(uint32_t *base_address, uint32_t *version, uint32_t flags);

// Get the address of region n within the SDRAM data beginning at base_address
uint32_t *config_get_region_start(uint32_t n, uint32_t *base_address);

// Read system region including application-specific words from region data
bool config_read_system_region(uint32_t *region, uint32_t flags, 
  uint32_t num_application_words, uint32_t *application_words);

// Test a bit in the system word
bool config_test_system_word_bit(uint32_t bit);

#endif  // CONFIG_H