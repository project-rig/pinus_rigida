#include "connector_generator.h"

// Common includes
#include "../common/log.h"
#include "../common/random/mars_kiss64.h"

//-----------------------------------------------------------------------------
// ConnectionBuilder::ConnectorGenerator::AllToAll
//-----------------------------------------------------------------------------
ConnectionBuilder::ConnectorGenerator::AllToAll::AllToAll(uint32_t *&)
{
  LOG_PRINT(LOG_LEVEL_INFO, "\t\tAll-to-all connector");
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::ConnectorGenerator::AllToAll::Generate(
  unsigned int, unsigned int maxRowSynapses, unsigned int numPostNeurons,
  unsigned int vertexPostSlice,
  MarsKiss64 &, uint32_t (&indices)[1024]) const
{
  if(numPostNeurons != maxRowSynapses)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Cannot generate all-to-all connection row num post neurons:%u != max row synapses:%u",
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

//-----------------------------------------------------------------------------
// ConnectionBuilder::ConnectorGenerator::OneToOne
//-----------------------------------------------------------------------------
ConnectionBuilder::ConnectorGenerator::OneToOne::OneToOne(uint32_t *&)
{
  LOG_PRINT(LOG_LEVEL_INFO, "\t\tOne-to-one connector");
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::ConnectorGenerator::OneToOne::Generate(
  unsigned int row, unsigned int maxRowSynapses, unsigned int numPostNeurons,
  unsigned int vertexPostSlice,
  MarsKiss64 &, uint32_t (&indices)[1024]) const
{
  // The column index relative to the start of this post slice that
  // corresponds to this row
  unsigned int offsetColumn = row - vertexPostSlice;
  unsigned int k = 0;
  // If that index is within this slice, add index to row
  if (offsetColumn >= 0 || offsetColumn < numPostNeurons)
    indices[k++] = offsetColumn;

  return k;
}

//-----------------------------------------------------------------------------
// ConnectionBuilder::ConnectorGenerator::FixedProbability
//-----------------------------------------------------------------------------
ConnectionBuilder::ConnectorGenerator::FixedProbability::FixedProbability(uint32_t *&region)
{
  m_Probability = *region++;

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tFixed-probability connector: probability:%u",
    m_Probability
  );
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::ConnectorGenerator::FixedProbability::Generate(
  unsigned int, unsigned int maxRowSynapses, unsigned int numPostNeurons,
  unsigned int vertexPostSlice,
  MarsKiss64 &rng, uint32_t (&indices)[1024]) const
{
  // Write indices
  unsigned int k = 0;
  for(unsigned int i = 0; i < numPostNeurons; i++)
  {
    // If draw if less than probability, add index to row
    if(rng.GetNext() < m_Probability)
    {
      indices[k++] = i;
    }
  }

  // If we have drawn less than the maximum number of synapses
  if(k <= maxRowSynapses)
  {
    return k;
  }
  // Otherwise give error and return maximum
  else
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Fixed probability connector generation has resulted in %u synapses but max is %u",
              k, maxRowSynapses);
    return maxRowSynapses;
  }
}
