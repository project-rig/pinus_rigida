#include "connector_generator.h"

// Rig CPP common includes
#include "rig_cpp_common/log.h"
#include "rig_cpp_common/random/mars_kiss64.h"

#include "../common/maths/hypergeometric.h"
#include "../common/maths/binomial.h"

using namespace Common::Maths;

//-----------------------------------------------------------------------------
// ConnectionBuilder::ConnectorGenerator::AllToAll
//-----------------------------------------------------------------------------
ConnectionBuilder::ConnectorGenerator::AllToAll::AllToAll(uint32_t *&region)
{
  m_AllowSelfConnections = *region++;

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tAll-to-all connector: Allow self connections: %u",
	    m_AllowSelfConnections);
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::ConnectorGenerator::AllToAll::Generate(
  unsigned int row, unsigned int numPostNeurons,
  unsigned int vertexPostSlice, unsigned int vertexPreSlice,
  MarsKiss64 &, uint32_t (&indices)[1024])
{
  // The column index on the diagonal for this row, i.e., the column to not
  // connect to if self connections are not allowed
  const int columnRelativeToPost = (int)row + (int)vertexPreSlice - (int)vertexPostSlice;

  // Write indices
  unsigned int i;
  unsigned int k = 0;
  for(i = 0; i < numPostNeurons; i++)
  {
    if (m_AllowSelfConnections || !(columnRelativeToPost >= 0 && i == ((unsigned int) columnRelativeToPost)))
    {
      indices[k++] = i;
    }
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
  unsigned int row, unsigned int numPostNeurons,
  unsigned int vertexPostSlice, unsigned int vertexPreSlice,
  MarsKiss64 &, uint32_t (&indices)[1024])
{
  // The column index on the diagonal for this row, i.e., the column to
  // connect to
  const int columnRelativeToPost = (int)row + (int)vertexPreSlice - (int)vertexPostSlice;

  unsigned int k = 0;
  // If that index is within this slice, add index to row
  if (columnRelativeToPost >= 0 || columnRelativeToPost < (int)numPostNeurons)
  {
    indices[k++] = (uint32_t)columnRelativeToPost;
  }
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
  unsigned int row, unsigned int numPostNeurons,
  unsigned int vertexPostSlice, unsigned int vertexPreSlice,
  MarsKiss64 &rng, uint32_t (&indices)[1024])
{
  // The column index on the diagonal for this row, i.e., the column to not
  // connect to if self connections are not allowed
  const int columnRelativeToPost = (int)row + (int)vertexPreSlice - (int)vertexPostSlice;

  // Write indices
  unsigned int i;
  unsigned int k = 0;
  for(i = 0; i < numPostNeurons; i++)
  {
    // If draw if less than probability, add index to row
    if(rng.GetNext() < m_Probability && (m_AllowSelfConnections || !(columnRelativeToPost >= 0 && i == ((unsigned int) columnRelativeToPost))))
    {
      indices[k++] = i;
    }
  }

  return k;
}

//-----------------------------------------------------------------------------
// ConnectionBuilder::ConnectorGenerator::FixedTotalNumber
//-----------------------------------------------------------------------------
ConnectionBuilder::ConnectorGenerator::FixedTotalNumber::FixedTotalNumber(uint32_t *&region)
{
  m_AllowSelfConnections = *region++;
  m_WithReplacement = *region++;
  m_ConnectionsInSubmatrix = *region++;
  m_SubmatrixSize = *region++;

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tFixed total number connector: connections in submatrix: %u %u",
            m_ConnectionsInSubmatrix, m_WithReplacement);
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::ConnectorGenerator::FixedTotalNumber::Generate(
  unsigned int, unsigned int numPostNeurons,
  unsigned int, unsigned int,
  MarsKiss64 &rng, uint32_t (&indices)[1024])
{
  unsigned int i;

  unsigned int numInRow;
  if (m_WithReplacement)
  {
    numInRow = Binomial(m_ConnectionsInSubmatrix,
      numPostNeurons,
      m_SubmatrixSize, rng);
  }
  else
  {
    numInRow = Hypergeom(m_ConnectionsInSubmatrix,
      m_SubmatrixSize - m_ConnectionsInSubmatrix,
      numPostNeurons, rng);
  }
  
  m_ConnectionsInSubmatrix -= numInRow;
  m_SubmatrixSize -= numPostNeurons;

  if (m_WithReplacement)
  {
    for(i=0; i<numInRow; i++)
    {
      unsigned int u01 = (rng.GetNext() & 0x00007fff);
      unsigned int j = (u01 * numPostNeurons) >> 15;
      indices[i] = j;
    }
  }
  else
  {
    // Reservoir sampling
    for(i=0; i<numInRow; i++)
    {
      indices[i] = i;
    }

    for(i=numInRow; i<numPostNeurons; i++)
    {
      // j = rand(0, i) (inclusive)
      unsigned int u01 = (rng.GetNext() & 0x00007fff);
      unsigned int j = (u01 * (i+1)) >> 15;
      if (j < numInRow)
      {
        indices[j] = i;
      }
    }
  }

  return numInRow;
}
