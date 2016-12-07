#include "connector_generator.h"

// Standard includes
#include <algorithm>

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

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tFixed total number connector: connections in submatrix: %u, "
            "with replacement: %u", m_ConnectionsInSubmatrix, m_WithReplacement);
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::ConnectorGenerator::FixedTotalNumber::Generate(
  unsigned int, unsigned int numPostNeurons,
  unsigned int, unsigned int,
  MarsKiss64 &rng, uint32_t (&indices)[1024])
{
  unsigned int i, u01, j, numInRow;

  // Determine how many of the submatrix connections are within this row
  // If there are no connections left to allocate to a row,
  // then there are no connections in this row
  if (m_ConnectionsInSubmatrix == 0)
  {
    numInRow = 0;
  }
  // If we're on the last row of the submatrix, then all of the remaining
  // submatrix connections get allocated to this row
  else if (numPostNeurons == m_SubmatrixSize)
  {
    numInRow = m_ConnectionsInSubmatrix;
  }
  // Otherwise, sample from the distribution over the number of the submatrix
  // connections that will end up within this row. The distribution depends
  // on whether the connections are made with or without replacement
  else
  {
    // Sample from a binomial distribution to determine how many of
    // the submatrix connections are within this row
    if (m_WithReplacement)
    {
      // Each of the connections has a (row size)/(submatrix size)
      // probability of ending up in this row
      numInRow = Binomial(m_ConnectionsInSubmatrix,
                          numPostNeurons,
                          m_SubmatrixSize, rng);
    }
    // Sample from a hypergeometric distribution to determine how many of
    // the submatrix connections are within this row
    else
    {
      // In the whole submatrix, there are some number of connections,
      // some number of non-connections, and our row is a random sample
      // of (row size) of them
      numInRow = Hypergeom(m_ConnectionsInSubmatrix,
                           m_SubmatrixSize - m_ConnectionsInSubmatrix,
                           numPostNeurons, rng);
    }
  }

  // Clamp numInRow down to buffer size
  numInRow = std::min<unsigned int>(numInRow, 1024);

  // Sample from the possible connections in this row numInRow times
  if (m_WithReplacement)
  {
    // Sample them with replacement
    for(i=0; i<numInRow; i++)
    {
      u01 = (rng.GetNext() & 0x00007fff);
      j = (u01 * numPostNeurons) >> 15;
      indices[i] = j;
    }
  }
  else
  {
    // Sample them without replacement using reservoir sampling
    for(i=0; i<numInRow; i++)
    {
      indices[i] = i;
    }
    for(i=numInRow; i<numPostNeurons; i++)
    {
      // j = rand(0, i) (inclusive)
      u01 = (rng.GetNext() & 0x00007fff);
      j = (u01 * (i+1)) >> 15;
      if (j < numInRow)
      {
        indices[j] = i;
      }
    }
  }

  m_ConnectionsInSubmatrix -= numInRow;
  m_SubmatrixSize -= numPostNeurons;

  return numInRow;
}
