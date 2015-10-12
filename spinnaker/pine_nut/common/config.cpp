#include "config.h"

// Standard includes
#include <cstring>

// Common includes
#include "log.h"

//-----------------------------------------------------------------------------
// Common::Config
//-----------------------------------------------------------------------------
namespace Common
{
bool Config::VerifyHeader(uint32_t *baseAddress, uint32_t, uint32_t &version) const
{
  if (baseAddress[0] != 0xAD130AD6)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "Magic number is %08x", baseAddress[0]);
    return false;
  }

  version = baseAddress[1]; // version number extracted.

  LOG_PRINT(LOG_LEVEL_INFO, "Magic = %08x, version = %u.%u", baseAddress[0],
    baseAddress[1] >> 16, baseAddress[1] & 0xFFFF);
  return true;
}
//-----------------------------------------------------------------------------
bool Config::ReadSystemRegion(uint32_t *region, uint32_t,
  unsigned int numApplicationWords, uint32_t applicationWords[])
{
  LOG_PRINT(LOG_LEVEL_INFO, "ReadSystemRegion: starting\n");

  // Read timer period and simulation ticks from first two words
  m_TimerPeriod = region[0];
  m_SimulationTicks = region[1];

  // Copy application words
  if(numApplicationWords > 0)
  {
    memcpy(applicationWords, &region[2],
      numApplicationWords * sizeof(uint32_t));
  }

  LOG_PRINT(LOG_LEVEL_INFO, "\ttimer period=%u, simulation ticks=%u\n",
    m_TimerPeriod, m_SimulationTicks);

  return true;
}
//-----------------------------------------------------------------------------
uint32_t *Config::GetBaseAddressAllocTag()
{
  // Get core and app ID from sark
  unsigned int coreID = sark_core_id();
  unsigned int appID = sark_app_id();

  // Find tag for this core's base address
  // **TODO** next SARK will have build in function to do this
  uint32_t *address = (uint32_t*)sv->alloc_tag[(appID << 8) + coreID];
  LOG_PRINT(LOG_LEVEL_INFO, "Based on allocated tag, SDRAM for app_id %u running on core %u begins at %08x", appID, coreID, address);
  return address;
}
}; // namespace Common