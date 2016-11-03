// Standard includes
#include <cstdint>
#include <climits>

// Common includes
#include "../arm_intrinsics.h"
#include "../fixed_point_number.h"

// Maths includes
#include "ln.h"

// Namespaces
using namespace Common::Maths;
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// Anonymous namespace
//-----------------------------------------------------------------------------
namespace
{
// ck = 1 + k/64
//
// Thus log_ck [k] = log (1 + k/64) + 12 in u5.27

const uint32_t g_LogCK [] =
  { 1610612736, 1612693673, 1614742838, 1616761188,
    1618749635, 1620709053, 1622640276, 1624544106,
    1626421307, 1628272616, 1630098736, 1631900343,
    1633678087, 1635432592, 1637164458, 1638874261,
    1640562556, 1642229879, 1643876743, 1645503644,
    1647111061, 1648699455, 1650269271, 1651820939,
    1653354872, 1654871473, 1656371128, 1657854212,
    1659321087, 1660772103, 1662207601, 1663627908,
    1665033342, 1666424211, 1667800815, 1669163444,
    1670512377, 1671847888, 1673170241, 1674479692,
    1675776492, 1677060882, 1678333097, 1679593367,
    1680841913, 1682078952, 1683304693, 1684519341,
    1685723096, 1686916150, 1688098693, 1689270907,
    1690432973, 1691585063, 1692727349, 1693859995,
    1694983162, 1696097009, 1697201687, 1698297348,
    1699384138, 1700462197, 1701531667, 1702592682,
    1703645376};

const int16_t g_RecipTable [] =
  {     0,  -1008,  -1986,  -2934,  -3855,  -4749,  -5617,  -6461,
    -7282,  -8080,  -8856,  -9612, -10348, -11065, -11763, -12444,
    -13107, -13754, -14386, -15002, -15604, -16191, -16765, -17326,
    -17873, -18409, -18933, -19445, -19946, -20436, -20916, -21385,
    -21845, -22296, -22737, -23169, -23593, -24008, -24415, -24815,
    -25206, -25590, -25967, -26337, -26700, -27056, -27406, -27749,
    -28087, -28418, -28744, -29064, -29378, -29687, -29991, -30290,
    -30583, -30872, -31156, -31436, -31711, -31982, -32248, -32510,
    -32768};

//! \brief This function performs a multiply-accumulate
//! \param[in] r accumulator value
//! \param[in] x one of the factors
//! \return r := r - x * log (2).
inline int32_t SubtractMultLog2 (int32_t r, int32_t x)
{
  return (r - x * 93032640);
}

//! \brief This function divides x by k/64; it uses the
//! Arm DSP instructions.
//! \param[in] x input value
//! \param[in] k the `breakpoint' index.
//! \return x/(k/64)

inline int32_t DivideCK(int32_t x, uint32_t k)
{
  return __smlawb(x, g_RecipTable[k], x);
}

inline int32_t CubicTerm(int32_t r)
{
  register int32_t t = __smultt (r, r);

  t = __smulwt(178958404*8, t);
  t = __smulwt(t, r);

  return (r + t);
}

inline uint32_t UInt32Round(uint32_t r, uint32_t n)
{
  r = (r >> n) + ((r >> (n-1)) & 0x1);

  return r;
}

//! \brief This function calculates a range-reduced log function.
//! \param[in] x is a u0.31 fraction.
//! \return A value representing log (1+x) in u5.27 (or s4.27) format.
inline uint32_t Log12(uint32_t x)
{
  register uint32_t k = UInt32Round(x, 26);
  register union {uint32_t u; int32_t i;} z;
  register int32_t r;

  //assert (k <= 64);

  z.u = x - (k << 26);

  // At this point z.i holds an s0.31 representation of the remainder
  // ... which is known to be in [-1/128, 1/128].

  r = DivideCK(z.i, k);

  // At this point r holds an s0.31 representation of the x/ck

  // The following approximation is outlined on page 72-3 of J-M Muller.
  // But, we have adapted the coefficients using sollya.
  //
  // log(r) = r + 44739601/2^29 * r^3
  //
  // However, since r is very small, the second term is _almost_
  // small enough to be ignored.

  r = CubicTerm(r);

  r = g_LogCK[k] + (r >> 5);

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
S1615 Ln(S1615 x)
{
  register int      shift = __builtin_clz (x);
  register uint32_t z     = ((uint32_t)(x)) << (shift + 1);

  // assert (x > 0);

  //log_info ("shift = %u, z = %R (%u), x = %k (%d)", shift, z >> 16, z, x, x);

  register int32_t r  = (int32_t)(Log12(z));

  //log_info ("r before: %k (%d)", r >> 12, r);

  r  = SubtractMultLog2(r, shift - 16);

  //log_info ("r shifted: %k (%d)", r >> 12, r);

  r  = UInt32Round(r, 12);            // round result from u5.27 to s16.15

  //log_info ("r after:  %k (%d)", r, r);

  r -= 393216;                          // subtract 12 * 2^15

  //assert (-340696 <= r && r <= 363409);

  return r;
}
} // Maths
} // Common