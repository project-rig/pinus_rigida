#include "matrix_generator.h"

// Connection builder includes
#include "connector_generator.h"
#include "param_generator.h"

//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator::Static
//-----------------------------------------------------------------------------
void ConnectionBuilder::MatrixGenerator::Static::Generate(uint32_t *matrixAddress,
  unsigned int maxRowSynapses, unsigned int weightFixedPoint, unsigned int numPostNeurons,
  const ConnectorGenerator::Base *connectorGenerator,
  const ParamGenerator::Base *delayGenerator,
  const ParamGenerator::Base *weightGenerator,
  MarsKiss64 &rng) const
{
  // Loop through rows
  for(uint32_t i = 0; i < m_NumRows; i++)
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "\tRow %u", i);

    // Generate row indices
    uint32_t indices[1024];
    LOG_PRINT(LOG_LEVEL_TRACE, "\t\tGenerating indices");
    const unsigned int numIndices = connectorGenerator->Generate(i, maxRowSynapses,
                                                                 numPostNeurons,
                                                                 rng, indices);

    // Generate delays and weights for each index
    int32_t delays[1024];
    int32_t weights[1024];
    LOG_PRINT(LOG_LEVEL_TRACE, "\t\tGenerating delays");
    delayGenerator->Generate(numIndices, weightFixedPoint, rng, delays);

    LOG_PRINT(LOG_LEVEL_TRACE, "\t\tGenerating weights");
    weightGenerator->Generate(numIndices, weightFixedPoint, rng, weights);

    // Write row length
    *matrixAddress++ = numIndices;

    // **TODO** support delay extension
    *matrixAddress++ = 0;
    *matrixAddress++ = 0;

    // Loop through synapses and write synaptic words
    for(unsigned int j = 0; j < numIndices; j++)
    {
      *matrixAddress++ = (indices[j] & IndexMask) |
        (((uint32_t)delays[j] & DelayMask) << IndexBits) |
        (weights[j] << (DelayBits + IndexBits));
    }

    // Skip end of row padding
    *matrixAddress += (maxRowSynapses - numIndices);
  }
}
