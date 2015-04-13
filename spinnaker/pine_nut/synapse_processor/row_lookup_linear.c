#include "row_lookup_linear.h"

// Standard includes
#include <string.h>

// Sark includes
#include <sark.h>

// Common includes
#include "../common/config.h"
#include "../common/log.h"
#include "../common/utils.h"

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
static uint32_t *synaptic_matrix_base = NULL;

//-----------------------------------------------------------------------------
// Module functions
//-----------------------------------------------------------------------------
static bool read_row_size_region(uint32_t *region, uint32_t flags)
{
  USE(flags);
  
  // Copy row size table
  memcpy(row_size, region, sizeof(uint32_t) * ROW_SIZE_TABLE_SIZE);

#if LOG_LEVEL <= LOG_LEVEL_INFO
  LOG_PRINT(LOG_LEVEL_INFO, "Row_size\n");
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
  USE(flags);
  
  // Copy master population table
  memcpy(master_population, region, sizeof(uint16_t) * MASTER_POPULATION_SIZE);

#if LOG_LEVEL <= LOG_LEVEL_INFO
  LOG_PRINT(LOG_LEVEL_INFO, "Master_population\n");
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
static bool read_synaptic_matrix_region(uint32_t *region, uint32_t flags)
{
  USE(flags);
  synaptic_matrix_base = region;
  
#if LOG_LEVEL <= LOG_LEVEL_INFO
  LOG_PRINT(LOG_LEVEL_INFO, "Synaptic matrix base address:%p\n", synaptic_matrix_base);
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
  
  if(!read_synaptic_matrix_region(
    config_get_region_start(region_synaptic_matrix, base_address), 
    flags))
  {
    return false;
  }
  
  
  return true;
}
//-----------------------------------------------------------------------------
bool row_lookup_get_address(uint32_t key, uint32_t **address, uint32_t *size_bytes)
{
  // **TODO** figure out key scheme
  uint32_t pid = key >> 10;
  uint32_t nid = key & 0x3FF;   // lowest 10 bits
  
  if(pid >= MASTER_POPULATION_SIZE)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Population ID %u too large to be supported by linear row lookup\n", pid);
    return false;
  }
  
  uint32_t master_population_entry = (uint32_t)(master_population[pid]);
  uint32_t size_index = master_population_entry & 0x7; // get lowest 3 bits into s;
  uint32_t population_offset_kilobytes = master_population_entry >> 3;  // d is now only 13 bits, i.e. 0..8095 .

  
  LOG_PRINT(LOG_LEVEL_TRACE, "Spike = %08x, pid = %u, size_index = %u, population_offset_kilobytes = %u, nid = %u",
    key, pid, size_index, population_offset_kilobytes, nid);

  if(size_index == 0)
  {
    LOG_PRINT(LOG_LEVEL_WARN, "Spike %u (= %x): population not found in master population table\n", 
      key, key);
    return false;
  }
  else
  {
    // Return size
    *size_bytes = row_size[size_index];
    
    uint32_t neuron_offset_bytes = nid * row_size[size_index];

    // **NOTE** 1024 converts from kilobyte offset to byte offset
    uint32_t population_offset_bytes = population_offset_kilobytes * 1024;

    LOG_PRINT(LOG_LEVEL_TRACE, "Neuron offset (bytes) = %u, population offset (bytes) = %u, base = %08x, size = %u\n", 
      neuron_offset_bytes, population_offset_bytes, synaptic_matrix_base, *size_bytes);
    
    // Return address
    *address = (uint32_t*)((uint32_t)synaptic_matrix_base + 
      population_offset_bytes + neuron_offset_bytes);
    
    return true;
  }
}