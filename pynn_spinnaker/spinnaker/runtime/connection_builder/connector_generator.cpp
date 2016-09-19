#include "connector_generator.h"

// Common includes
#include "../common/random/mars_kiss64.h"

//-----------------------------------------------------------------------------
// ConnectionBuilder::ConnectorGenerator::AllToAll
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::ConnectorGenerator::AllToAll::Generate(
  unsigned int, unsigned int maxRowSynapses, unsigned int numPostNeurons,
  MarsKiss64 &rng, uint32_t (&indices)[1024]) const
{
  if(numPostNeurons != maxRowSynapses)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "\tCannot generate all-to-all connection row num post neurons:%u != max row synapses:%u",
      numPostNeurons, maxRowSynapses);
    return 0;
  }

  // Write indices
  for(unsigned int i = 0; i < numPostNeurons; i++)
  {
    indices[i] = i;
  }

  return numPostNeurons;
}