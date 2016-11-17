// Common includes
#include "rig_cpp_common/fixed_point_number.h"

// Maths includes
#include "rig_cpp_common/maths/ln.h"
#include "logfact.h"

// Namespaces
using namespace Common::Maths;
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// Anonymous namespace
//-----------------------------------------------------------------------------
namespace
{

// Log factorial for arguments 0-63
const S1615 logFact[64] = {
  0,0,22713,58712,104138,156876,215588,279352,347491,419490,494941,573515,
  654941,738989,825465,914203,1005055,1097894,1192605,1289089,1387253,1487016,
  1588303,1691047,1795186,1900662,2007423,2115421,2224611,2334950,2446401,
  2558925,2672491,2787064,2902616,3019118,3136542,3254865,3374061,3494109,
  3614986,3736673,3859149,3982396,4106396,4231133,4356589,4482751,4609603,
  4737130,4865319,4994157,5123631,5253730,5384441,5515753,5647656,5780139,
  5913191,6046804,6180967,6315673,6450911,6586673
};
}

//-----------------------------------------------------------------------------
// Common::Maths
//-----------------------------------------------------------------------------
namespace Common
{
namespace Maths
{

// Log factorial
S1615 LogFact(uint32_t n)
{
  if (n < 64) // Lookup table for argument values 0-63
    return logFact[n];  
  else
  {
    S1615 n1 = (S1615)(n << 15);
    // Stirling approximation
    // (n+0.5)*log(n) - n + 0.5*log(2*pi)
    return MulS1615((n1 + 16384), Ln(n1))  - n1 + 30111;
  }
}
    
} // Maths
} // Common
