#include "matrix_generator.h"

// Common includes
#include "../common/log.h"

// Connection builder includes
#include "connector_generator.h"
#include "param_generator.h"

//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator::Base
//-----------------------------------------------------------------------------
ConnectionBuilder::MatrixGenerator::Base::Base(uint32_t *&region)
{
  m_SignedWeight = *region++;
}
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
  unsigned int vertexPostSlice, unsigned int vertexPreSlice,
  const ConnectorGenerator::Base *connectorGenerator,
  const ParamGenerator::Base *delayGenerator,
  const ParamGenerator::Base *weightGenerator,
  uint32_t (&indices)[1024], int32_t (&delays)[1024], int32_t (&weights)[1024],
  MarsKiss64 &rng) const
{
  LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\tGenerating indices");
  const unsigned int numIndices = connectorGenerator->Generate(row, maxRowSynapses,
                                                               numPostNeurons,
							       vertexPostSlice,
							       vertexPreSlice,
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
ConnectionBuilder::MatrixGenerator::Static::Static(uint32_t *&region) : Base(region)
{
  LOG_PRINT(LOG_LEVEL_INFO, "\t\tStatic synaptic matrix: %u signed weights",
    IsSignedWeight());
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::MatrixGenerator::Static::Generate(uint32_t *matrixAddress,
  unsigned int maxRowSynapses, unsigned int weightFixedPoint,
  unsigned int numPostNeurons, unsigned int numRows,
  unsigned int vertexPostSlice, unsigned int vertexPreSlice,
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
      maxRowSynapses, weightFixedPoint, numPostNeurons, vertexPostSlice, vertexPreSlice,
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
      // Clamp delays and weights
      delays[j] = ClampDelay(delays[j]);
      weights[j] = ClampWeight(weights[j]);

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
ConnectionBuilder::MatrixGenerator::Plastic::Plastic(uint32_t *&region) : Base(region)
{
  // Read number of presynaptic state words from region
  const uint32_t preStateBytes = *region++;
  m_SynapseTraceBytes = *region++;

  // Round up to words
  m_PreStateWords = (preStateBytes / 4)
      + (((preStateBytes & 3) != 0) ? 1 : 0);

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tPlastic synaptic matrix: %u signed weights, %u bytes presynaptic state (%u words), %u bytes synapse trace",
            IsSignedWeight(), preStateBytes, m_PreStateWords, m_SynapseTraceBytes);
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::MatrixGenerator::Plastic::Generate(uint32_t *matrixAddress,
  unsigned int maxRowSynapses, unsigned int weightFixedPoint,
  unsigned int numPostNeurons, unsigned int numRows,
  unsigned int vertexPostSlice, unsigned int vertexPreSlice,
  const ConnectorGenerator::Base *connectorGenerator,
  const ParamGenerator::Base *delayGenerator,
  const ParamGenerator::Base *weightGenerator,
  MarsKiss64 &rng) const
{
  // Calculate the number of words required to contain control array
  const unsigned int maxControlArrayWords = (maxRowSynapses / 2)
    + (((maxRowSynapses & 1) != 0) ? 1 : 0);

  // Calculate the number of words required to contain synapse array
  const unsigned int maxPlasticArrayBytes = maxRowSynapses * (2 + m_SynapseTraceBytes);
  const unsigned int maxPlasticArrayWords = (maxPlasticArrayBytes / 4)
    + (((maxPlasticArrayBytes & 3) != 0) ? 1 : 0);
  LOG_PRINT(LOG_LEVEL_INFO, "\t\tMax control array words:%u, Max synapse array words:%u",
            maxControlArrayWords, maxPlasticArrayWords);

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
      maxRowSynapses, weightFixedPoint, numPostNeurons, vertexPostSlice, vertexPreSlice,
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
    const unsigned int numSynapseArrayBytes = numIndices * (2 + m_SynapseTraceBytes);
    const unsigned int numPlasticArrayWords = (numSynapseArrayBytes / 4)
      + (((numSynapseArrayBytes & 3) != 0) ? 1 : 0);

    // From this get 8-bit pointer to synapses and 16-bit pointer to control half words
    uint8_t *synapseAddress = reinterpret_cast<uint8_t*>(matrixAddress);
    uint16_t *controlAddress = reinterpret_cast<uint16_t*>(matrixAddress + numPlasticArrayWords);

    // Loop through synapses
    for(unsigned int j = 0; j < numIndices; j++)
    {
      // Clamp delays and weights
      delays[j] = ClampDelay(delays[j]);
      weights[j] = ClampWeight(weights[j]);

      // Write weight to first two synapse bytes
      uint16_t *weightAddress = reinterpret_cast<uint16_t*>(synapseAddress);
      *weightAddress = (uint16_t)weights[j];

      // Go onto next synapse
      synapseAddress += 2;

      // Write synapse trace bytes
      for(unsigned int s = 0; s < m_SynapseTraceBytes; s++)
      {
        *synapseAddress++ = 0;
      }

      // Build control word
      const uint16_t controlWord = (uint16_t)(indices[j] & IndexMask) |
        (((uint32_t)delays[j] & DelayMask) << IndexBits);

#if LOG_LEVEL <= LOG_LEVEL_TRACE
      io_printf(IO_BUF, "%u/%u,", weights[j], controlWord);
#endif
      // Write control word
      *controlAddress++ = controlWord;
    }

#if LOG_LEVEL <= LOG_LEVEL_TRACE
    io_printf(IO_BUF, "\n");
#endif

    // Advance over synapse and control half words; and padding to next word
    matrixAddress += (maxControlArrayWords + maxPlasticArrayWords);
  }

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tGenerated %u synapses", numSynapses);
}
