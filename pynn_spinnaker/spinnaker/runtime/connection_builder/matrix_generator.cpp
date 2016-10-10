#include "matrix_generator.h"

// Common includes
#include "../common/log.h"

// Connection builder includes
#include "connector_generator.h"
#include "param_generator.h"

//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator::Static
//-----------------------------------------------------------------------------
void ConnectionBuilder::MatrixGenerator::Base::TraceUInt(uint32_t (&values)[1024],
                                                         unsigned int number) const
{
#if LOG_LEVEL <= LOG_LEVEL_TRACE
  for(unsigned int i = 0; i < number; i++)
  {
    io_printf(IO_BUF, "%u,", values[i]);
  }
  io_printf(IO_BUF, "\n");
#endif
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::MatrixGenerator::Base::TraceInt(int32_t (&values)[1024],
                                                        unsigned int number) const
{
#if LOG_LEVEL <= LOG_LEVEL_TRACE
  for(unsigned int i = 0; i < number; i++)
  {
    io_printf(IO_BUF, "%u,", values[i]);
  }
  io_printf(IO_BUF, "\n");
#endif
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::MatrixGenerator::Base::GenerateRow(unsigned int row,
  unsigned int maxRowSynapses, unsigned int weightFixedPoint, unsigned int numPostNeurons,
  const ConnectorGenerator::Base *connectorGenerator,
  const ParamGenerator::Base *delayGenerator,
  const ParamGenerator::Base *weightGenerator,
  uint32_t (&indices)[1024], int32_t (&delays)[1024], int32_t (&weights)[1024],
  MarsKiss64 &rng) const
{
  LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\tGenerating indices");
  const unsigned int numIndices = connectorGenerator->Generate(row, maxRowSynapses,
                                                                numPostNeurons,
                                                                rng, indices);
  TraceUInt(indices, numIndices);
  
  // Generate delays for each index
  LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\tGenerating delays");
  delayGenerator->Generate(numIndices, 0, rng, delays);
  TraceInt(delays, numIndices);

  // Generate weights for each index
  LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\tGenerating weights");
  weightGenerator->Generate(numIndices, weightFixedPoint, rng, weights);
  TraceInt(weights, numIndices);

  // Return row length
  return numIndices;
}

//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator::Static
//-----------------------------------------------------------------------------
ConnectionBuilder::MatrixGenerator::Static::Static(uint32_t *&region)
{
  LOG_PRINT(LOG_LEVEL_INFO, "\t\tStatic synaptic matrix");
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::MatrixGenerator::Static::Generate(uint32_t *matrixAddress,
  unsigned int maxRowSynapses, unsigned int weightFixedPoint,
  unsigned int numPostNeurons, unsigned int numRows,
  const ConnectorGenerator::Base *connectorGenerator,
  const ParamGenerator::Base *delayGenerator,
  const ParamGenerator::Base *weightGenerator,
  MarsKiss64 &rng) const
{
  // Loop through rows
  unsigned int numSynapses = 0;
  for(unsigned int i = 0; i < numRows; i++)
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\tRow %u (%08x)", i, matrixAddress);

    // Generate indices, weights and delays for row
    uint32_t indices[1024];
    int32_t delays[1024];
    int32_t weights[1024];
    const unsigned int numIndices = GenerateRow(i,
      maxRowSynapses, weightFixedPoint, numPostNeurons,
      connectorGenerator, delayGenerator, weightGenerator, indices, delays, weights,
      rng);

    // Update total number of synapses
    numSynapses += numIndices;

    // Write row length
    *matrixAddress++ = numIndices;

    // **TODO** support delay extension
    *matrixAddress++ = 0;
    *matrixAddress++ = 0;

    // Loop through synapses
    for(unsigned int j = 0; j < numIndices; j++)
    {
      // Static synaptic matrices are unsigned
      // so if weight is negative, flip sign
      if(weights[j] < 0)
      {
        weights[j] = -weights[j];
      }

      // Build synaptic word
      const uint32_t word = (indices[j] & IndexMask) |
        (((uint32_t)delays[j] & DelayMask) << IndexBits) |
        (weights[j] << (DelayBits + IndexBits));

#if LOG_LEVEL <= LOG_LEVEL_TRACE
      io_printf(IO_BUF, "%u,", word);
#endif
      // Write word to matrix
      *matrixAddress++ = word;
    }

#if LOG_LEVEL <= LOG_LEVEL_TRACE
    io_printf(IO_BUF, "\n");
#endif

    // Advance over padding to next row
    matrixAddress += (maxRowSynapses - numIndices);
  }

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tGenerated %u synapses", numSynapses);
}

//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator::Plastic
//-----------------------------------------------------------------------------
ConnectionBuilder::MatrixGenerator::Plastic::Plastic(uint32_t *&region)
{
  // Read number of presynaptic state words from region
  const uint32_t preStateBytes = *region++;

  // Round up to words
  m_PreStateWords = (preStateBytes / 4)
      + (((preStateBytes & 3) != 0) ? 1 : 0);

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tPlastic synaptic matrix: %u bytes presynaptic state (%u words)",
            preStateBytes, m_PreStateWords);
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::MatrixGenerator::Plastic::Generate(uint32_t *matrixAddress,
  unsigned int maxRowSynapses, unsigned int weightFixedPoint,
  unsigned int numPostNeurons, unsigned int numRows,
  const ConnectorGenerator::Base *connectorGenerator,
  const ParamGenerator::Base *delayGenerator,
  const ParamGenerator::Base *weightGenerator,
  MarsKiss64 &rng) const
{
  const unsigned int maxArrayWords = (maxRowSynapses / 2)
      + (((maxRowSynapses & 1) != 0) ? 1 : 0);

  // Loop through rows
  unsigned int numSynapses = 0;
  for(unsigned int i = 0; i < numRows; i++)
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\tRow %u (%08x)", i, matrixAddress);

    // Generate indices, weights and delays for row
    uint32_t indices[1024];
    int32_t delays[1024];
    int32_t weights[1024];
    const unsigned int numIndices = GenerateRow(i,
      maxRowSynapses, weightFixedPoint, numPostNeurons,
      connectorGenerator, delayGenerator, weightGenerator, indices, delays, weights,
      rng);

    // Update total number of synapses
    numSynapses += numIndices;

    // Write row length
    *matrixAddress++ = numIndices;

    // **TODO** support delay extension
    *matrixAddress++ = 0;
    *matrixAddress++ = 0;

    // Zero presynaptic state words
    for(unsigned int w = 0; w < m_PreStateWords; w++)
    {
      *matrixAddress++ = 0;
    }

    // Calculate the size of each array (fixed and plastic) in words
    const unsigned int numArrayWords = (numIndices / 2)
      + (((numIndices & 1) != 0) ? 1 : 0);

    // From this get 16-bit pointers to weight and control half words
    uint16_t *weightAddress = reinterpret_cast<uint16_t*>(matrixAddress);
    uint16_t *controlAddress = reinterpret_cast<uint16_t*>(matrixAddress + numArrayWords);

    // Loop through synapses
    for(unsigned int j = 0; j < numIndices; j++)
    {
      // Static synaptic matrices are unsigned
      // so if weight is negative, flip sign
      if(weights[j] < 0)
      {
        weights[j] = -weights[j];
      }

      // Write weight
      *weightAddress++ = (uint16_t)weights[j];

      // Build control word
      const uint16_t controlWord = (uint16_t)(indices[j] & IndexMask) |
        (((uint32_t)delays[j] & DelayMask) << IndexBits);

#if LOG_LEVEL <= LOG_LEVEL_TRACE
      io_printf(IO_BUF, "%u/%u,", weight, controlWord);
#endif
      // Write control word
      *controlAddress++ = controlWord;
    }

#if LOG_LEVEL <= LOG_LEVEL_TRACE
    io_printf(IO_BUF, "\n");
#endif

    // Advance over weight and control half words and padding to next word
    matrixAddress += (2 * maxArrayWords);
  }

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tGenerated %u synapses", numSynapses);
}
