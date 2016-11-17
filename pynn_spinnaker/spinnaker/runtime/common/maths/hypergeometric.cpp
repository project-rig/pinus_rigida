#include "hypergeometric.h"

// Common includes
#include "rig_cpp_common/fixed_point_number.h"
#include "rig_cpp_common/random/mars_kiss64.h"
#include "logfact.h"
#include "rig_cpp_common/maths/ln.h"
#include "rig_cpp_common/maths/exp.h"

// Namespaces
using namespace Common::Maths;
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// Anonymous namespace
//-----------------------------------------------------------------------------
namespace
{

// Sample from a hypergeometric distribution with the given parameters
// Inverse transform sampling method
// Since the number of times through the loop is the value returned,
// the expected execution time is proportional to
// nsample * (ngood / (ngood+nbad))
uint32_t randhg_hin_core(uint32_t ngood, uint32_t nbad, uint32_t nsample,
                         MarsKiss64 &rng)
{
  uint32_t n = ngood + nbad, x;
  S1615 ln_p, p, u;

  // We can never sample a value greater than either ngood or nsample
  uint32_t maxval = (ngood < nsample) ? ngood : nsample;

  do
  {

  // The log probability of returning the first value
  if(nsample < nbad)
  {
    ln_p = LogFact(nbad) - LogFact(n) + LogFact(n-nsample) - LogFact(nbad-nsample);
    x = 0;
  }
  else
  {
    ln_p = LogFact(ngood) - LogFact(n) + LogFact(nsample) - LogFact(nsample-nbad);
    x = nsample - nbad;
  }
  // Offset the log probability so that the format of the probability p
  // uses 30 fractional bits
  ln_p += 340695;

  // Sample from a uniform distribution [0, 1]
  // Note, we're actually using 30 bits for the fractional part
  u = (S1615)(rng.GetNext() & 0x3fffffff);

  // For successive possible values to return, subtract the probability
  // of returning that value from u. When u <= p, return the current value x
  p = ExpS1615(ln_p);
  while(u > p)
  {
    u -= p;
    // The log probability of x calculated in terms of the log probability
    // of (x-1)
    ln_p += Ln(ngood-x);
    ln_p -= Ln(x+1);
    ln_p += Ln(nsample-x);
    ln_p -= Ln(nbad-nsample+1+x);
    p = ExpS1615(ln_p);
    x++;
    if(x > maxval)
      break;
  }

  // With small probability, x might exceed maxval before u <= p,
  // due to numerical issues. If this happens repeat the procedure
  } while (x > maxval);

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

// Sample from a hypergeometric distribution with the given parameters
uint32_t Hypergeom(uint32_t ngood, uint32_t nbad, uint32_t nsample, MarsKiss64 &rng)
{
  if(ngood <= nbad)
  {
    if((2 * nsample) <= (ngood + nbad))
    {
      return randhg_hin_core(ngood, nbad, nsample, rng);
    }
    else
    {
      // If the sample is more than half of the total number, sample
      // ntotal - nsample instead, and subtract the result from ngood,
      // which is more efficient and gives the same distribution
      return ngood - randhg_hin_core(ngood, nbad, ngood + nbad - nsample, rng);
    }
  }
  // If ngood > nbad, swap ngood and nbad and subtract the sampled value from
  // nsample, which is more efficient and gives the same distribution
  else
  {
    if((2 * nsample) <= (ngood + nbad))
    {
      return nsample - randhg_hin_core(nbad, ngood, nsample, rng);
    }
    else
    {
      return nsample - nbad + randhg_hin_core(nbad, ngood, ngood+nbad-nsample, rng);
    }
  }
}

} // Maths
} // Common
