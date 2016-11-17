#include "binomial.h"

// Common includes
#include "rig_cpp_common/fixed_point_number.h"
#include "rig_cpp_common/random/mars_kiss64.h"
#include "rig_cpp_common/maths/ln.h"
#include "recip.h"

// Namespaces
using namespace Common::Maths;
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// Anonymous namespace
//-----------------------------------------------------------------------------
namespace
{

// Sample from the binomial distribution with the given parameters, where
// ln_1_min_p = log(1-p)
// Geometric method by L. Devroye (1980)
// Since the number of times through the loop is the value returned,
// expected execution time is proportional to n*p
uint32_t randbin_bg_core(uint32_t n, S1615 ln_1_min_p,
                         MarsKiss64 &rng)
{
  uint32_t y = 0, x = 0;
  if (ln_1_min_p >= 0)
    return x;

  S1615 recip_ln_1_min_p = Reciprocal(ln_1_min_p);

  while (1)
  {
    // Strip off the sign bit of u
    S1615 u = (S1615)(rng.GetNext() & 0x7fffffff);
    // Subtract an offset from Ln(u) so it's the log of a uniform
    // random variate in [0,1] with 15 fractional bits
    y += (MulS1615(Ln(u) - 363408, recip_ln_1_min_p) >> 15) + 1;
    if (y > n)
      break;
    x += 1;
  }

  return x;
}

} // anonymous namespace

//-----------------------------------------------------------------------------
// Common::Maths
//-----------------------------------------------------------------------------
namespace Common
{
namespace Maths
{

// Sample from the binomial distribution with the given parameters
uint32_t Binomial(uint32_t n, S1615 p, MarsKiss64 &rng)
{
  if (p > 16384)
  {
    // If p > 0.5, sample from the binomial with 1-p, subtract the result
    // from n. This is more efficient, and gives the same distribution.
    return n - randbin_bg_core(n, Ln(p), rng);
  }
  else
  {
    return randbin_bg_core(n, Ln(32768-p), rng);
  }
}

// Sample from the binomial distribution with the given parameters,
// where p is rational and given as a numerator and denominator
// Since we pass log(1-p) to randbin_bg_core, replace this with
// log((denom - num)/denom) = log(denom-num) - log(denom) in case we can't represent
// p given the resolution of our fixed point types.
uint32_t Binomial(uint32_t n, uint32_t num, uint32_t denom, MarsKiss64 &rng)
{
  if ((num<<1) > denom)
  {
    // If p > 0.5, sample from the binomial with 1-p, subtract the result
    // from n. This is more efficient, and gives the same distribution.
    return n - randbin_bg_core(n, Ln((int32_t)num) - Ln((int32_t)denom), rng);
  }
  else
  {
    return randbin_bg_core(n, Ln((int32_t)denom-(int32_t)num) - Ln((int32_t)denom), rng);
  }
}

} // Maths
} // Common
