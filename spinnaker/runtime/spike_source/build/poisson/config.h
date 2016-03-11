#pragma once

// Model includes
#include "../../../common/random/mars_kiss64.h"
#include "../../../common/poisson_source.h"

namespace SpikeSource
{
//-----------------------------------------------------------------------------
// Typedefines
//-----------------------------------------------------------------------------
typedef Common::PoissonSource<MarsKiss64> Source;
};