#pragma once

// Standard includes
#include <cstdint>

//-----------------------------------------------------------------------------
// Common::Random::MarsKiss64
//-----------------------------------------------------------------------------
namespace Common
{
namespace Random
{
class MarsKiss64
{
public:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const unsigned int SeedSize = 4;

  MarsKiss64() : m_Seed{123456789, 987654321, 43219876, 6543217}
  {
  }

  MarsKiss64(const uint32_t(&seed)[SeedSize])
  {
    SetSeed(seed);
  }

  //-----------------------------------------------------------------------------
  // Operators
  //-----------------------------------------------------------------------------
  uint32_t operator()()
  {
    m_Seed[0] = 314527869 * m_Seed[0] + 1234567;
    m_Seed[1] ^= m_Seed[1] << 5;
    m_Seed[1] ^= m_Seed[1] >> 7;
    m_Seed[1] ^= m_Seed[1] << 22;
    uint64_t t = 4294584393ULL * m_Seed[2] + m_Seed[3];
    m_Seed[3] = t >> 32;
    m_Seed[2] = t;

    return ((uint32_t)m_Seed[0] + m_Seed[1] + m_Seed[2]);
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  void SetSeed(const uint32_t(&seed)[SeedSize])
  {
    // y (<- seed[2]) can't be zero so set to arbitrary non-zero if so
    // avoid z=c=0 and make < 698769069
    m_Seed[0] = seed[0];
    m_Seed[1] = (seed[1] == 0) ? 13031301 : seed[1];
    m_Seed[2] = seed[2];
    m_Seed[3] = seed[3] % 698769068 + 1;
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint32_t m_Seed[SeedSize];
};
} // Random
} // Common