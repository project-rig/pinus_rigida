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
  for(uint32_t i = 0; i < numRows; i++)
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\tRow %u (%08x)", i, matrixAddress);

    // Generate row indices
    uint32_t indices[1024];
    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\tGenerating indices");
    const unsigned int numIndices = connectorGenerator->Generate(i, maxRowSynapses,
                                                                 numPostNeurons,
                                                                 rng, indices);
    TraceUInt(indices, numIndices);

    // Generate delays for each index
    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\tGenerating delays");
    int32_t delays[1024];
    delayGenerator->Generate(numIndices, 0, rng, delays);
    TraceInt(delays, numIndices);

    // Generate weights for each index
    int32_t weights[1024];
    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\tGenerating weights");
    weightGenerator->Generate(numIndices, weightFixedPoint, rng, weights);
    TraceInt(weights, numIndices);

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

    // Skip end of row padding
    matrixAddress += (maxRowSynapses - numIndices);
  }
}
