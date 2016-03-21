#include "config.h"

// Common includes
#include "log.h"
#include "spinnaker.h"

//-----------------------------------------------------------------------------
// Common::Config
//-----------------------------------------------------------------------------
namespace Common
{
bool Config::VerifyHeader(const uint32_t *baseAddress, uint32_t) const
{
  if (baseAddress[0] != 0xAD130AD6)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Magic number is %08x", baseAddress[0]);
    return false;
  }
  else
  {
    return true;
  }
}
//-----------------------------------------------------------------------------
bool Config::ReadSystemRegion(const uint32_t *region, uint32_t,
  unsigned int numApplicationWords, uint32_t applicationWords[])
{
  LOG_PRINT(LOG_LEVEL_INFO, "ReadSystemRegion");

  // Read timer period and simulation ticks from first two words
  m_TimerPeriod = region[0];
  m_SimulationTicks = region[1];

  // Copy application words
  if(numApplicationWords > 0)
  {
    spin1_memcpy(applicationWords, &region[2],
      numApplicationWords * sizeof(uint32_t));
  }

  LOG_PRINT(LOG_LEVEL_INFO, "\ttimer period=%u, simulation ticks=%u",
    m_TimerPeriod, m_SimulationTicks);

  return true;
}
//-----------------------------------------------------------------------------
uint32_t *Config::GetBaseAddressAllocTag()
{
  // Get core and app ID from sark
  unsigned int coreID = sark_core_id();

  // Find tag for this core's base address
  uint32_t *address = (uint32_t*)sark_tag_ptr(coreID, 0);
  LOG_PRINT(LOG_LEVEL_INFO, "Based on allocated tag, SDRAM for core %u begins at %08x",
            coreID, address);
  return address;
}
}; // namespace Common