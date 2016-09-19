#include "connector_generator.h"

// Common includes
#include "../common/random/mars_kiss64.h"

//-----------------------------------------------------------------------------
// ConnectionBuilder::ConnectorGenerator::AllToAll
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::ConnectorGenerator::AllToAll::Generate(unsigned int,
  unsigned int maxRowWords, MarsKiss64 &, uint32_t (&indices)[1024]) const
{
  // Write indices
  for(unsigned int i = 0; i < maxRowWords; i++)
  {
    indices[i] = i;
  }

  return maxRowWords;
}