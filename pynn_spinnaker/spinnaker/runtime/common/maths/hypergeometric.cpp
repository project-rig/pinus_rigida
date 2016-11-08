#include "hypergeometric.h"

// Common includes
#include "../fixed_point_number.h"
#include "../random/mars_kiss64.h"
#include "logfact.h"
#include "ln.h"
#include "exp.h"

// Namespaces
using namespace Common::Maths;
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// Anonymous namespace
//-----------------------------------------------------------------------------
namespace
{

uint32_t randhg_hin_core(uint32_t ngood, uint32_t nbad, uint32_t nsample,
			 MarsKiss64 &rng)
{	
  uint32_t n = ngood + nbad, x;
  S1615 ln_p, p, u;

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
	
  u = (S1615)(rng.GetNext() & 0x00007FFF);

  p = ExpS1615(ln_p);
  while(u > p)
  {
    u -= p;
    ln_p += Ln((ngood-x) << 15);
    ln_p -= Ln((x+1) << 15);
    ln_p += Ln((nsample-x) << 15);
    ln_p -= Ln((nbad-nsample+1+x) << 15);
    p = ExpS1615(ln_p);
    x++;
    if(x == n)
      break;      // TODO error?
  }

  if (x > n)
    x = n;

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

uint32_t Hypergeom(uint32_t ngood, uint32_t nbad, uint32_t nsample, MarsKiss64 &rng)
{
  if(ngood <= nbad)
  {
    if((2 * nsample) <= (ngood + nbad))
      return randhg_hin_core(ngood, nbad, nsample, rng);
    else
      return ngood - randhg_hin_core(ngood, nbad, ngood + nbad - nsample, rng);
  }
  else
  {
    if((2 * nsample) <= (ngood + nbad))
      return nsample - randhg_hin_core(nbad, ngood, nsample, rng);
    else
      return nsample - nbad + randhg_hin_core(nbad, ngood, ngood+nbad-nsample, rng);
  }
}
  
} // Maths
} // Common
