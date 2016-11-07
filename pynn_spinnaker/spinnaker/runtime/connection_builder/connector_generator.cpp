#include "connector_generator.h"

// Common includes
#include "../common/log.h"
#include "../common/random/mars_kiss64.h"
#include "../common/maths/hypergeometric.h"

// Namespaces
using namespace Common::Maths;

//-----------------------------------------------------------------------------
// ConnectionBuilder::ConnectorGenerator::AllToAll
//-----------------------------------------------------------------------------
ConnectionBuilder::ConnectorGenerator::AllToAll::AllToAll(uint32_t *&region)
{
  m_AllowSelfConnections = *region++;

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tAll-to-all connector");
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::ConnectorGenerator::AllToAll::Generate(
  unsigned int row, unsigned int maxRowSynapses, unsigned int numPostNeurons,
  unsigned int vertexPostSlice, unsigned int vertexPreSlice,
  MarsKiss64 &, uint32_t (&indices)[1024])
{
  if(numPostNeurons != maxRowSynapses)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Cannot generate all-to-all connection row num post neurons:%u != max row synapses:%u",
      numPostNeurons, maxRowSynapses);
    return 0;
  }

  // The column index on the diagonal for this row, i.e., the column to not
  // connect to if self connections are not allowed
  int columnRelativeToPost = (int)row + (int)vertexPreSlice - (int)vertexPostSlice;

  // Write indices
  unsigned int k = 0;
  for(unsigned int i = 0; i < numPostNeurons; i++)
  {
    if (m_AllowSelfConnections || i != columnRelativeToPost)
      indices[k++] = i;
  }

  return k;
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
  unsigned int vertexPostSlice, unsigned int vertexPreSlice,
  MarsKiss64 &, uint32_t (&indices)[1024])
{
  // The column index on the diagonal for this row, i.e., the column to
  // connect to
  int columnRelativeToPost = (int)row + (int)vertexPreSlice - (int)vertexPostSlice;

  unsigned int k = 0;
  // If that index is within this slice, add index to row
  if (columnRelativeToPost >= 0 || columnRelativeToPost < numPostNeurons)
    indices[k++] = columnRelativeToPost;

  return k;
}

//-----------------------------------------------------------------------------
// ConnectionBuilder::ConnectorGenerator::FixedProbability
//-----------------------------------------------------------------------------
ConnectionBuilder::ConnectorGenerator::FixedProbability::FixedProbability(uint32_t *&region)
{
  m_AllowSelfConnections = *region++;
  m_Probability = *region++;

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tFixed-probability connector: probability:%u",
    m_Probability);
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::ConnectorGenerator::FixedProbability::Generate(
  unsigned int row, unsigned int maxRowSynapses, unsigned int numPostNeurons,
  unsigned int vertexPostSlice, unsigned int vertexPreSlice,
  MarsKiss64 &rng, uint32_t (&indices)[1024])
{
  // The column index on the diagonal for this row, i.e., the column to not
  // connect to if self connections are not allowed
  int columnRelativeToPost = (int)row + (int)vertexPreSlice - (int)vertexPostSlice;

  // Write indices
  unsigned int k = 0;
  for(unsigned int i = 0; i < numPostNeurons; i++)
  {
    // If draw if less than probability, add index to row
    if(rng.GetNext() < m_Probability &&
       (m_AllowSelfConnections || i != columnRelativeToPost))
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

//-----------------------------------------------------------------------------
// ConnectionBuilder::ConnectorGenerator::FixedTotalNumber
//-----------------------------------------------------------------------------
ConnectionBuilder::ConnectorGenerator::FixedTotalNumber::FixedTotalNumber(uint32_t *&region)
{
  m_AllowSelfConnections = *region++;
  m_ConnectionsInSubmatrix = *region++;
  m_SubmatrixSize = *region++;

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tFixed total number connector: connections in submatrix: %u",
    m_ConnectionsInSubmatrix);
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::ConnectorGenerator::FixedTotalNumber::Generate(
  unsigned int row, unsigned int maxRowSynapses, unsigned int numPostNeurons,
  unsigned int vertexPostSlice, unsigned int vertexPreSlice,
  MarsKiss64 &rng, uint32_t (&indices)[1024])
{
  unsigned int i;
  unsigned int numInRow = Hypergeom(m_ConnectionsInSubmatrix,
				    m_SubmatrixSize - m_ConnectionsInSubmatrix,
				    numPostNeurons, rng);
  m_ConnectionsInSubmatrix -= numInRow;
  m_SubmatrixSize -= numPostNeurons;

  // Reservoir sampling
  for(i=0; i<numInRow; i++)
    indices[i] = i;
  for(i=numInRow; i<numPostNeurons; i++)
  {
    // j = rand(0, i) (inclusive)
    unsigned int u01 = (rng.GetNext() & 0x00007fff);
    unsigned int j = (u01 * (i+1)) >> 15;
    if (j < numInRow)
      indices[j] = i;
  }

  return numInRow;
}
