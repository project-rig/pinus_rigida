#include "config.h"

// SARK includes
#include <sark.h>

//-----------------------------------------------------------------------------
// File variables
//-----------------------------------------------------------------------------
static uint32_t system_word = 0;
static uint32_t timer_period = 0;
static uint32_t simulation_ticks = 0;

//-----------------------------------------------------------------------------
// File inline functions
//-----------------------------------------------------------------------------
static inline address_t address_word_offset(address_t address, uint32_t offset)
{
  return (& address[address[offset] >> 2]); 
}
//-----------------------------------------------------------------------------
static inline bool check_magic_number(uint32_t magic_number) 
{ 
  return (magic_number == 0xAD130AD6); 
}

//-----------------------------------------------------------------------------
// Global functions
//-----------------------------------------------------------------------------
uint32_t *config_get_base_address()
{
  // Get core and app ID from sark
  uint core_id = sark_core_id();
  uint app_id = sark_app_id();
  
  // Find tag for this core's base address
  // **TODO** next SARK will have build in function to do this
  uint32_t *address = (uint32_t*)sv->alloc_tag[(app_id << 8) + core_id];
  log_info("Based on allocated tag, SDRAM for app_id %u running on core %u begins at %08x", app_id, core_id, address);
  return address;
}
//-----------------------------------------------------------------------------
bool config_read_header(uint32_t *base_address, uint32_t *version, uint32_t flags)
{
  use(flags);

  if (!check_magic_number(base_address[0])) 
  {
    log_info("magic number is %08x", base_address[0]);
    return (false);
  }

  *version = base_address[1]; // version number extracted.

  log_info("magic = %08x, version = %d.%d", base_address[0],
    base_address[1] >> 16, base_address[1] & 0xFFFF);
  return (true);
}
//-----------------------------------------------------------------------------
uint32_t *config_get_region_start (uint32_t n, uint32_t *base_address)
{ 
  return (address_word_offset(address, 2 + n));  
}
//-----------------------------------------------------------------------------
bool config_read_system_region(uint32_t *region, uint32_t flags, 
  uint32_t num_application_words, uint32_t *application_words)
{
  use(flags);

  log_info("system_region_filled: starting");
  
  // Read timer period and simulation ticks from first two words
  timer_period = region[1];
  simulation_ticks = region[2];

  // Copy application words
  if(num_application_words > 0)
  {
    memcpy(application_words, &region[3], 
      num_application_words * sizeof(uint32_t);
  }
  
  log_info("\ttimer period=%u, simulation ticks=%u, system word=%08x", 
    timer_period, simulation_ticks, system_word);

  return (true);
}
//-----------------------------------------------------------------------------
bool config_test_system_word_bit(uint32_t bit)
{
  return ((system_word & bit) != 0);
}




