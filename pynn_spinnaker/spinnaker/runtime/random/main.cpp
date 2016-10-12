#include <cstdint>

// Common includes
#include "../common/fixed_point_number.h"
#include "../common/log.h"
#include "../common/spinnaker.h"
#include "../common/maths/normal.h"
#include "../common/random/mars_kiss64.h"

// Namespaces
using namespace Common;
using namespace Common::Maths;
using namespace Common::Random;

//-----------------------------------------------------------------------------
// Entry point
//-----------------------------------------------------------------------------
extern "C" void c_main()
{
  MarsKiss64 rng;

  static const unsigned int numSamples = 20000;
  LOG_PRINT(LOG_LEVEL_INFO, "Generating %u random numbers", numSamples);

  for(unsigned int i = 0; i < numSamples; i++)
  {
    uint32_t uniform = rng.GetNext();
    S1615 normal = NormalU032(uniform);

    io_printf(IO_BUF, "%u,%k,\n", uniform, normal);
  }

}

