#include "connector_generators.h"

//-----------------------------------------------------------------------------
// AllToAll
//-----------------------------------------------------------------------------
unsigned int MatrixGenerator::ConnectorGenerators::Generate(unsigned int, unsigned int maxRowWords,
                                                            MarsKiss64 &, uint32_t (&indices)[1024]) const
{
  // Write indices
  for(unsigned int i = 0; i < maxRowWords; i++)
  {
    indices[i] = i;
  }

  return maxRowWords;
}