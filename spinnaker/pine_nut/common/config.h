#pragma once

// Standard includes
#include <cstdint>

//-----------------------------------------------------------------------------
// Common::Config
//-----------------------------------------------------------------------------
namespace Common
{
class Config
{
public:
  //-----------------------------------------------------------------------------
  // Public methods
  //-----------------------------------------------------------------------------
  // Verify header residing at the beginning of all executable's SDRAM data
  bool VerifyHeader(const uint32_t *baseAddress, uint32_t flags) const;

  // Read system region including application-specific words from region data
  bool ReadSystemRegion(const uint32_t *region, uint32_t flags,
    unsigned int numApplicationWords, uint32_t applicationWords[]);

  uint32_t GetTimerPeriod() const
  {
    return m_TimerPeriod;
  }

  uint32_t GetSimulationTicks() const
  {
    return m_SimulationTicks;
  }

  //-----------------------------------------------------------------------------
  // Static methods
  //-----------------------------------------------------------------------------
  // Get the base address of this core's SDRAM data using allocation tag
  static uint32_t *GetBaseAddressAllocTag();

  // Get the address of region n within the SDRAM data beginning at base_address
  // **NOTE** one is added to skip over magic number
  static uint32_t *GetRegionStart(uint32_t *baseAddress, unsigned int regionNumber)
  {
     return &baseAddress[baseAddress[1 + regionNumber] >> 2];
  }

private:
  //-----------------------------------------------------------------------------
  // Private members
  //-----------------------------------------------------------------------------
  uint32_t m_TimerPeriod;
  uint32_t m_SimulationTicks;
};
} // namespace Common