#pragma once

// Standard includes
#include <cstdint>
#include "../spinnaker.h"

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
  static const unsigned int StateSize = 4;

  MarsKiss64() : m_State{123456789, 987654321, 43219876, 6543217}
  {
  }

  MarsKiss64(const uint32_t(&state)[StateSize])
  {
    SetState(state);
  }

  //-----------------------------------------------------------------------------
  // Operators
  //-----------------------------------------------------------------------------
  uint32_t GetNext()
  {
    m_State[0] = 314527869 * m_State[0] + 1234567;
    m_State[1] ^= m_State[1] << 5;
    m_State[1] ^= m_State[1] >> 7;
    m_State[1] ^= m_State[1] << 22;
    uint64_t t = 4294584393ULL * m_State[2] + m_State[3];
    m_State[3] = t >> 32;
    m_State[2] = t;

    return ((uint32_t)m_State[0] + m_State[1] + m_State[2]);
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  void SetState(const uint32_t(&seed)[StateSize])
  {
    // y (<- seed[2]) can't be zero so set to arbitrary non-zero if so
    // avoid z=c=0 and make < 698769069
    m_State[0] = seed[0];
    m_State[1] = (seed[1] == 0) ? 13031301 : seed[1];
    m_State[2] = seed[2];
    m_State[3] = seed[3] % 698769068 + 1;
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint32_t m_State[StateSize];
};
} // Random
} // Common