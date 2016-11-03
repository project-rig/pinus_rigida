// Standard includes
#include <climits>

// Common includes
#include "../arm_intrinsics.h"
#include "../fixed_point_number.h"

// Maths includes
#include "exp.h"
#include "polynomial.h"
#include "round.h"

// Namespaces
using namespace Common::Maths;
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// Anonymous namespace
//-----------------------------------------------------------------------------
namespace
{

// The following array has entry [n]
const uint64_t g_ExpHi[26] =
  {9708,  26389,         71733,        194991,         530041,        1440801,
        3916503,      10646160,      28939262,       78665070,      213833830,
      581260615,    1580030169,    4294967296,    11674931555,    31735754293,
    86266724208,  234497268814,  637429664642,  1732713474316,  4710003551159,
 12803117065094,34802480465680,94602950235157,257157480542844,699026506411923};

const uint32_t g_ExpMid[16] =
  {         0,  260218914,  504671961,  734314346,
    950043403, 1152702096, 1343082321, 1521927990,
   1689937949, 1847768698, 1996036966, 2135322113,
   2266168400, 2389087112, 2504558555, 2613033936};

const uint32_t g_ExpSeries[3] = { 5294, 4293434720, 2081624032};

// the following calculates a series expansion
// for 1 - exp (-x/2^15) for x in [0..2^11 - 1]

uint32_t CoefMult (uint32_t c, uint32_t x)
{
  uint64_t tmp = ((uint64_t)c * (uint64_t)x) >> 32;

  return ((uint32_t)(tmp));
}

uint32_t ExpSeries (uint32_t x)
{
  uint32_t tmp  = g_ExpSeries[1] - CoefMult(g_ExpSeries[2], x);
  tmp  = CoefMult(tmp, x);
  tmp += g_ExpSeries [0];

  return tmp;
}

//! \brief This function returns the most significant 32-bit word of a 64-bit
//! unsigned integer.
//! \param[in] x The 64-bit number
//! \return The most significant 32-bits of x.
uint32_t High(uint64_t x)
{
  return (uint32_t)(x >> 32);
}

//! \brief This function returns the least significant 32-bit word of a 64-bit
//! unsigned integer.
//! \param[in] x The 64-bit number
//! \return The least significant 32-bits of x.
uint32_t Low(uint64_t x)
{
  return High(x << 32);
}

//! \brief The function treats the 64-bit number as if it were a 32-bit integer
//! and a 32-bit fraction, rounding the fractional part.
//! \param[in] x The 64-bit number
//! \return The rounded result.
uint64_t Round64 (uint64_t x)
{
  uint64_t r = (uint64_t)(High(x));

  if (Low(x) >= INT32_MAX)
  {
    r++;
  }

  return r;
}

//! \brief The function scales the 64-bit number \p x, treating \p y as if it
//! were an unsigned long fract, rounding the fractional part.
//! \param[in] x A 64-bit unsigned integer.
//! \param[in] y A 32-bit unsigned integer treated as if it is an
//! unsigned long fract.
//! \return The rounded result.
static inline uint64_t Scale64 (uint64_t x, uint32_t y)
{
  uint64_t r = Round64((uint64_t)(Low(x)) * (uint64_t)(y));

  r += (uint64_t)(High(x)) * (uint64_t)(y);

  return r;
}
}


//-----------------------------------------------------------------------------
// Common::Maths
//-----------------------------------------------------------------------------
namespace Common
{
namespace Maths
{
S1615 ExpS1615(S1615 v)
{
  if(v > 363408)
  {
    return INT32_MAX; // overflow saturation
  }
  else if(v < -340695)
  {
     return 0;         // overflow saturation
  }
  else
  {
    int32_t z = v >> 15;       // truncated integer part.
    int32_t f = v - (z << 15); // fractional remainder

    uint64_t tmp1;
    if (f > 0)
    {
      z = z + 1;
      f = 32768 - f;

      tmp1  = g_ExpHi[13+z];
      tmp1 -= Scale64 (tmp1, g_ExpMid[f >> 11]);

      uint32_t y = ((uint32_t)(f & 0x7FF)) << 17;

      tmp1 -= Scale64 (tmp1, ExpSeries(y));
    }
    else
    {// (f == 0)
      tmp1 = g_ExpHi[13+z];
    }

    return (int32_t)(tmp1 >> 17);
  }

}
} // Maths
} // Common