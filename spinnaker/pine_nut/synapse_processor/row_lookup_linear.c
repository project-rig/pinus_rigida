#include "row_lookup_linear.h"

// Standard includes
#include <string.h>

// Common includes
#include "config.h"
#include "log.h"

// Synapse processor includes
#include "synapse_processor.h"

//-----------------------------------------------------------------------------
// Macros
//-----------------------------------------------------------------------------
#define MASTER_POPULATION_SIZE  1152
#define ROW_SIZE_TABLE_SIZE     8

//-----------------------------------------------------------------------------
// Module variables
//-----------------------------------------------------------------------------
static uint16_t master_population[MASTER_POPULATION_SIZE];
static uint32_t row_size[ROW_SIZE_TABLE_SIZE];

//-----------------------------------------------------------------------------
// Module functions
//-----------------------------------------------------------------------------
static bool read_row_size_region(uint32_t *region, uint32_t flags)
{
  // Copy row size table
  memcpy(row_size, region, sizeof(uint32_t) * ROW_SIZE_TABLE_SIZE;

#if LOG_LEVEL <= LOG_LEVEL_INFO
  LOG_PRINT(LOG_LEVEL_INFO, "row_size\n");
  LOG_PRINT(LOG_LEVEL_INFO, "------------------------------------------\n");
  for(uint32_t i = 0; i < ROW_SIZE_TABLE_SIZE; i++)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "\tindex %2u, size = %3u\n", i, row_size[i]);
  }
  LOG_PRINT(LOG_LEVEL_INFO, "------------------------------------------\n");
#endif
  
  return true;
}
//-----------------------------------------------------------------------------
static bool read_master_population_region(uint32_t *region, uint32_t flags)
{
  // Copy master population table
  memcpy(master_population, region, sizeof(uint16_t) * MASTER_POPULATION_SIZE);

#if LOG_LEVEL <= LOG_LEVEL_INFO
  LOG_PRINT(LOG_LEVEL_INFO, "master_population\n");
  LOG_PRINT(LOG_LEVEL_INFO, "------------------------------------------\n");
  for (uint32_t i = 0; i < MASTER_POPULATION_MAX; i++)
  {
    uint32_t mp = (uint32_t)(master_population[i]);
    uint32_t s  = mp & 0x7;
    if (s != 0)
    {
      LOG_PRINT(LOG_LEVEL_INFO, "\tindex %u, entry: %4u (13 bits = %04x), size = %3u\n",
        i, mp, mp >> 3, row_size_table [s]);
    }
  }
  LOG_PRINT(LOG_LEVEL_INFO, "------------------------------------------\n");
#endif
  
  return true;
}

//-----------------------------------------------------------------------------
// Global functions
//-----------------------------------------------------------------------------
bool row_lookup_read_sdram_data(uint32_t *base_address, uint32_t flags)
{
  if(!read_row_size_region(
    config_get_region_start(region_row_size, base_address), 
    flags))
  {
    return false;
  }
  
  if(!read_master_population_region(
    config_get_region_start(region_master_population, base_address), 
    flags))
  {
    return false;
  }
  
  return true;
}
//-----------------------------------------------------------------------------
bool row_lookup_get_address(uint32_t key, uint32_t *address, uint32_t *size_bytes)
{
  // **TODO** figure out key scheme
  uint32_t pid = make_pid (key_x (key), key_y (key), key_p (key));
  uint32_t nid = key &  KEY_MASK;   // lowest 10 bits
 
  check((pid < MASTER_POPULATION_MAX), "0 <= population_id (%u) < %u", pid,  MASTER_POPULATION_MAX);

  uint32_t d = (uint32_t)(master_population[pid]);
  uint32_t size_index = d & 0x7; // get lowest 3 bits into s;
  d = d >> 3;  // d is now only 13 bits, i.e. 0..8095 .

  
  //LOG_PRINT_TRACE("spike = %08x, pid = %u, s = %u, d = %u, nid = %u",
  //  key, pid, s, d, nid);

  if(s == 0)
  {
    LOG_PRINT(LOG_LEVEL_WARN, "Spike %u (= %x): population not found in master population table", key, key);
  }
  else
  {
    // Return size
    *size_bytes = row_size_table[size_index];
    
    uint32_t neuron_offset = nid * row_size_table[size_index];

    // **NOTE** 1024 converts from kilobyte offset to byte offset
    uint32_t population_offset = d * 1024;

    LOG_PRINT(LOG_LEVEL_TRACE, "stride = %u, neuron offset = %u, population offset = %u, base = %08x, size = %u\n", 
      stride, neuron_offset, population_offset, synaptic_row_base, *size_bytes);
    
    // Return address
    *address = (uint32_t*) ((uint32_t)synaptic_row_base + population_offset + neuron_offset);
  }

  return (s);
}